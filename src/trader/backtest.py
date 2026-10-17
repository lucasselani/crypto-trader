"""Backtest barra a barra, só comprado, com taxas, slippage e stop com trailing.
Um ativo (`run_backtest`) ou uma carteira dividindo o mesmo caixa (`run_portfolio`).

Ordem dos eventos em cada barra i:
1. Na abertura, executa a ordem gerada pelo sinal do fechamento de i-1.
2. Durante a barra, se a mínima tocar o stop, sai no stop (ou na abertura, se abriu abaixo dele).
3. No fechamento, marca o patrimônio, sobe o trailing stop e avalia os sinais para i+1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from trader.risk import RiskConfig, drawdown, position_size
from trader.strategies import Strategy

SECONDS_PER_YEAR = 365 * 24 * 3600


@dataclass
class CostModel:
    fee_rate: float = 0.001  # taxa por lado (Binance spot sem desconto: 0,1%)
    slippage: float = 0.0005  # deslize adverso por execução (0,05%)


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    ret: float
    reason: str
    symbol: str = ""


@dataclass
class BacktestResult:
    strategy: str
    params: dict
    equity: pd.Series
    trades: list[Trade]
    metrics: dict = field(default_factory=dict)

    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([t.__dict__ for t in self.trades])


def bars_per_year(index: pd.DatetimeIndex) -> float:
    if len(index) < 2:
        return 365.0
    step = pd.Series(index).diff().median().total_seconds()
    return SECONDS_PER_YEAR / step


def compute_metrics(
    equity: pd.Series, trades: list[Trade], exposure: float, close: pd.Series
) -> dict:
    eq = equity.dropna()
    if len(eq) < 2:
        return {"trades": len(trades)}
    bpy = bars_per_year(eq.index)
    total = eq.iloc[-1] / eq.iloc[0] - 1
    years = len(eq) / bpy
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1 if eq.iloc[-1] > 0 else -1.0
    max_dd = float((eq / eq.cummax() - 1).min())
    rets = eq.pct_change().dropna()
    sharpe = float(rets.mean() / rets.std() * np.sqrt(bpy)) if rets.std() > 0 else 0.0
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl <= 0]
    pf = sum(wins) / -sum(losses) if losses and sum(losses) < 0 else float("inf") if wins else 0.0
    c = close.loc[eq.index]
    months = (eq.index[-1] - eq.index[0]).days / 30.4375
    monthly = (eq.iloc[-1] / eq.iloc[0]) ** (1 / months) - 1 if eq.iloc[-1] > 0 and months else 0.0
    return {
        "total_return": float(total),
        "cagr": float(cagr),
        "monthly": float(monthly),
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else 0.0,
        "trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "profit_factor": float(pf),
        "avg_trade": float(np.mean([t.ret for t in trades])) if trades else 0.0,
        "exposure": exposure,
        "buy_hold": float(c.iloc[-1] / c.iloc[0] - 1),
    }


@dataclass
class _Book:
    """Estado de um ativo durante a simulação."""

    sig: pd.DataFrame
    o: np.ndarray
    lo: np.ndarray
    c: np.ndarray
    atr: np.ndarray
    entry: np.ndarray
    exit: np.ndarray
    rows: np.ndarray  # linha do ativo em cada timestamp da carteira (-1 = sem candle)
    qty: float = 0.0
    stop: float = np.nan
    cost_basis: float = 0.0
    entry_px: float = 0.0
    entry_t: pd.Timestamp | None = None
    pending: str | None = None
    last_close: float = np.nan


def run_portfolio(
    data: dict[str, pd.DataFrame],
    strategy: Strategy,
    *,
    initial_cash: float = 10_000.0,
    costs: CostModel | None = None,
    risk: RiskConfig | None = None,
    trade_from: pd.Timestamp | None = None,
    kill_switch: bool = True,
) -> BacktestResult:
    """Simula a carteira como o agente opera: vários ativos dividindo o mesmo caixa, no máximo
    `risk.max_open_positions` posições, tamanho pelo patrimônio total e, com `kill_switch`,
    sem novas entradas depois de um drawdown maior que `risk.max_drawdown`.

    Na abertura de cada barra executa primeiro as vendas (liberam caixa) e depois as compras,
    na ordem de `data`. `trade_from` limita as operações (e a curva) a partir dessa data."""
    costs = costs or CostModel()
    risk = risk or RiskConfig()
    index = pd.DatetimeIndex(sorted(set().union(*(df.index for df in data.values()))))
    books: dict[str, _Book] = {}
    for sym, df in data.items():
        sig = strategy.generate(df)
        books[sym] = _Book(
            sig, *(sig[k].to_numpy(float) for k in ("open", "low", "close", "atr")),
            sig["entry"].to_numpy(bool), sig["exit"].to_numpy(bool), sig.index.get_indexer(index),
        )

    warm = [b.sig.index[strategy.warmup] for b in books.values() if len(b.sig) > strategy.warmup]
    trades: list[Trade] = []
    if not warm:
        return BacktestResult(strategy.name, strategy.params(), pd.Series(dtype=float), trades)
    start = int(index.searchsorted(min(warm)))
    if trade_from is not None:
        start = max(start, int(index.searchsorted(trade_from)))

    cash, peak, killed, killed_at = initial_cash, initial_cash, False, None
    equity = np.full(len(index), np.nan)
    bars_in = 0

    def close_position(sym: str, b: _Book, t: pd.Timestamp, fill: float, reason: str) -> None:
        nonlocal cash
        proceeds = b.qty * fill * (1 - costs.fee_rate)
        pnl = proceeds - b.cost_basis
        trades.append(Trade(b.entry_t, t, b.entry_px, fill, b.qty, pnl, pnl / b.cost_basis,
                            reason, sym))
        cash += proceeds
        b.qty, b.stop = 0.0, np.nan

    for k in range(start, len(index)):
        t = index[k]
        live = [(s, b, int(b.rows[k])) for s, b in books.items() if b.rows[k] >= 0]

        for s, b, r in live:
            if b.pending == "sell" and b.qty > 0:
                close_position(s, b, t, b.o[r] * (1 - costs.slippage), "signal")
        equity_now = cash + sum(b.qty * b.last_close for b in books.values() if b.qty > 0)
        for s, b, r in live:
            if b.pending != "buy" or b.qty > 0 or killed or np.isnan(b.atr[r - 1]):
                continue
            if sum(1 for x in books.values() if x.qty > 0) >= risk.max_open_positions:
                continue
            fill = b.o[r] * (1 + costs.slippage)
            stop_px = fill - strategy.stop_atr_mult * b.atr[r - 1]
            q = position_size(equity_now, fill, stop_px, cash, risk, costs.fee_rate)
            if q > 0:
                b.cost_basis = q * fill * (1 + costs.fee_rate)
                cash -= b.cost_basis
                b.qty, b.stop, b.entry_px, b.entry_t = q, stop_px, fill, t
        for _, b, _ in live:
            b.pending = None

        for s, b, r in live:
            if b.qty > 0 and b.lo[r] <= b.stop:
                close_position(s, b, t, min(b.o[r], b.stop) * (1 - costs.slippage), "stop")
            if b.qty > 0:
                b.stop = max(b.stop, b.c[r] - strategy.stop_atr_mult * b.atr[r])
            b.last_close = b.c[r]

        if any(b.qty > 0 for b in books.values()):
            bars_in += 1
        equity[k] = cash + sum(b.qty * b.last_close for b in books.values() if b.qty > 0)
        peak = max(peak, equity[k])
        if kill_switch and not killed and drawdown(equity[k], peak) > risk.max_drawdown:
            killed, killed_at = True, t

        for _, b, r in live:
            if b.qty > 0 and b.exit[r]:
                b.pending = "sell"
            elif b.qty == 0 and b.entry[r]:
                b.pending = "buy"

    for s, b in books.items():
        if b.qty > 0:
            close_position(s, b, index[-1], b.last_close * (1 - costs.slippage), "end")
    equity[-1] = cash

    eq = pd.Series(equity, index).dropna()
    bench = pd.concat({s: b.sig["close"] for s, b in books.items()}, axis=1).reindex(index).ffill()
    result = BacktestResult(strategy.name, strategy.params(), eq, trades)
    result.metrics = compute_metrics(eq, trades, bars_in / max(1, len(index) - start),
                                     bench.iloc[:, 0])
    if len(books) > 1:
        # buy & hold de referência: carteira igualmente dividida entre os ativos
        rel = bench.loc[eq.index].bfill()
        result.metrics["buy_hold"] = float((rel.iloc[-1] / rel.iloc[0]).mean() - 1)
    if kill_switch:
        result.metrics["killed_at"] = killed_at.isoformat() if killed_at is not None else None
    return result


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    *,
    initial_cash: float = 10_000.0,
    costs: CostModel | None = None,
    risk: RiskConfig | None = None,
    trade_from: pd.Timestamp | None = None,
) -> BacktestResult:
    """Backtest de um único ativo (sem kill switch). `trade_from` limita as operações (e a curva)
    a partir dessa data, usando as barras anteriores só como aquecimento dos indicadores."""
    return run_portfolio({"": df}, strategy, initial_cash=initial_cash, costs=costs, risk=risk,
                         trade_from=trade_from, kill_switch=False)
