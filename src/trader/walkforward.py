"""Walk-forward: otimiza numa janela, testa na seguinte (fora da amostra), avança e repete.

Só o resultado fora da amostra (OOS) conta. Se ele for muito pior que o dentro da amostra,
a estratégia está sobreajustada. Aceita um ativo (DataFrame) ou uma carteira (dict).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import pandas as pd

from trader.backtest import BacktestResult, compute_metrics, run_portfolio
from trader.strategies import Strategy


def param_grid(grid: dict[str, list]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in itertools.product(*grid.values())]


@dataclass
class Window:
    train_start: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    params: dict
    in_sample: dict
    out_of_sample: dict


@dataclass
class WalkForwardResult:
    strategy: str
    windows: list[Window]
    equity: pd.Series
    metrics: dict = field(default_factory=dict)

    def windows_frame(self) -> pd.DataFrame:
        rows = []
        for w in self.windows:
            rows.append({
                "test_start": w.test_start.date(),
                "test_end": w.test_end.date(),
                "params": w.params,
                "is_calmar": round(w.in_sample.get("calmar", 0.0), 2),
                "oos_return": round(w.out_of_sample.get("total_return", 0.0), 4),
                "oos_trades": w.out_of_sample.get("trades", 0),
            })
        return pd.DataFrame(rows)


@dataclass
class Criteria:
    """Régua inicial para aprovar uma estratégia, sempre medida fora da amostra.
    Ponto de partida para ajustar com dados, não verdade absoluta."""

    min_calmar: float = 1.0  # ganho anual / pior queda
    min_profit_factor: float = 1.3  # ganho das vencedoras / perda das perdedoras
    min_trades: int = 30  # menos que isso é sorte demais para tirar conclusão
    min_positive_windows: float = 0.5  # fração das janelas com operações que terminaram no lucro


def evaluate(result: WalkForwardResult, criteria: Criteria | None = None) -> dict[str, bool]:
    c = criteria or Criteria()
    m = result.metrics
    traded = [w for w in result.windows if w.out_of_sample.get("trades", 0) > 0]
    positive = sum(1 for w in traded if w.out_of_sample.get("total_return", 0) > 0)
    checks = {
        "calmar": m.get("calmar", 0.0) >= c.min_calmar,
        "profit_factor": m.get("profit_factor", 0.0) >= c.min_profit_factor,
        "trades": m.get("trades", 0) >= c.min_trades,
        "positive_windows": bool(traded) and positive / len(traded) >= c.min_positive_windows,
    }
    checks["approved"] = all(checks.values())
    return checks


def _score(result: BacktestResult, objective: str, min_trades: int) -> float:
    m = result.metrics
    if m.get("trades", 0) < min_trades:
        return float("-inf")
    return float(m.get(objective, float("-inf")))


def optimize(
    data: dict[str, pd.DataFrame],
    candidates: list[Strategy],
    *,
    objective: str = "calmar",
    min_trades: int = 3,
    kill_switch: bool = False,
    fallback: Strategy | None = None,
    **bt_kwargs,
) -> tuple[Strategy, BacktestResult]:
    """Melhor candidata no período `data` pelo `objective`. Se nenhuma operar o suficiente, usa
    `fallback` (ou a primeira candidata)."""
    scored = [(s, run_portfolio(data, s, kill_switch=kill_switch, **bt_kwargs)) for s in candidates]
    best, best_res = max(scored, key=lambda sr: _score(sr[1], objective, min_trades))
    if _score(best_res, objective, min_trades) == float("-inf"):
        fb = fallback or candidates[0]
        return fb, run_portfolio(data, fb, kill_switch=kill_switch, **bt_kwargs)
    return best, best_res


def walk_forward(
    data: pd.DataFrame | dict[str, pd.DataFrame],
    base: Strategy,
    *,
    train_bars: int = 730,
    test_bars: int = 180,
    grid: dict[str, list] | None = None,
    objective: str = "calmar",
    min_trades: int = 3,
    kill_switch: bool = False,
    **bt_kwargs,
) -> WalkForwardResult:
    if isinstance(data, pd.DataFrame):
        data = {"": data}
    index = pd.DatetimeIndex(sorted(set().union(*(df.index for df in data.values()))))
    combos = param_grid(grid if grid is not None else type(base).grid) or [{}]
    candidates = [base.with_params(**p) for p in combos]
    warmup = max(s.warmup for s in candidates)
    if train_bars <= warmup:
        raise ValueError(f"train_bars ({train_bars}) precisa ser maior que o aquecimento ({warmup})")

    def window(a: int, b: int) -> dict[str, pd.DataFrame]:
        lo, hi = index[a], index[b] if b < len(index) else None
        out = {s: df[(df.index >= lo) & ((df.index < hi) if hi is not None else True)]
               for s, df in data.items()}
        return {s: df for s, df in out.items() if len(df)}

    def run(d: dict, s: Strategy, **kw) -> BacktestResult:
        return run_portfolio(d, s, kill_switch=kill_switch, **bt_kwargs, **kw)

    windows: list[Window] = []
    oos_parts: list[pd.Series] = []
    oos_trades = []
    for k in range(train_bars, len(index) - 1, test_bars):
        train = window(k - train_bars, k)
        best, best_res = optimize(train, candidates, objective=objective, min_trades=min_trades,
                                  kill_switch=kill_switch, fallback=base, **bt_kwargs)

        test_end = min(k + test_bars, len(index))
        res = run(window(max(0, k - best.warmup - 1), test_end), best, trade_from=index[k])
        windows.append(Window(
            index[k - train_bars], index[k], index[test_end - 1],
            {key: best.params()[key] for key in combos[0]},
            best_res.metrics, res.metrics,
        ))
        if len(res.equity):
            oos_parts.append(res.equity / res.equity.iloc[0])
            oos_trades.extend(res.trades)

    equity = pd.Series(dtype=float)
    level = 1.0
    for part in oos_parts:
        equity = pd.concat([equity, part * level])
        level = float(equity.iloc[-1])
    equity = equity[~equity.index.duplicated(keep="last")]

    result = WalkForwardResult(base.name, windows, equity)
    if len(equity) > 1:
        closes = pd.concat({s: df["close"] for s, df in data.items()}, axis=1).ffill()
        result.metrics = compute_metrics(equity, oos_trades, float("nan"), closes.iloc[:, 0])
        rel = closes.reindex(equity.index).bfill()
        result.metrics["buy_hold"] = float((rel.iloc[-1] / rel.iloc[0]).mean() - 1)
    return result
