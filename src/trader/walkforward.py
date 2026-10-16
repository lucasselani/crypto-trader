"""Walk-forward: otimiza numa janela, testa na seguinte (fora da amostra), avança e repete.

Só o resultado fora da amostra (OOS) conta. Se ele for muito pior que o dentro da amostra,
a estratégia está sobreajustada.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import pandas as pd

from trader.backtest import BacktestResult, compute_metrics, run_backtest
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


def _score(result: BacktestResult, objective: str, min_trades: int) -> float:
    m = result.metrics
    if m.get("trades", 0) < min_trades:
        return float("-inf")
    return float(m.get(objective, float("-inf")))


def walk_forward(
    df: pd.DataFrame,
    base: Strategy,
    *,
    train_bars: int = 730,
    test_bars: int = 180,
    grid: dict[str, list] | None = None,
    objective: str = "calmar",
    min_trades: int = 3,
    **bt_kwargs,
) -> WalkForwardResult:
    combos = param_grid(grid if grid is not None else type(base).grid) or [{}]
    candidates = [base.with_params(**p) for p in combos]
    warmup = max(s.warmup for s in candidates)
    if train_bars <= warmup:
        raise ValueError(f"train_bars ({train_bars}) precisa ser maior que o aquecimento ({warmup})")

    windows: list[Window] = []
    oos_parts: list[pd.Series] = []
    oos_trades = []
    for test_start in range(train_bars, len(df) - 1, test_bars):
        train = df.iloc[test_start - train_bars : test_start]
        scored = [(s, run_backtest(train, s, **bt_kwargs)) for s in candidates]
        best, best_res = max(scored, key=lambda sr: _score(sr[1], objective, min_trades))
        if _score(best_res, objective, min_trades) == float("-inf"):
            best, best_res = base, run_backtest(train, base, **bt_kwargs)

        test_end = min(test_start + test_bars, len(df))
        test_df = df.iloc[max(0, test_start - best.warmup - 1) : test_end]
        res = run_backtest(test_df, best, trade_from=df.index[test_start], **bt_kwargs)
        windows.append(Window(
            train.index[0], df.index[test_start], df.index[test_end - 1],
            {k: best.params()[k] for k in (combos[0] if combos[0] else {})},
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
        result.metrics = compute_metrics(equity, oos_trades, float("nan"), df["close"])
    return result
