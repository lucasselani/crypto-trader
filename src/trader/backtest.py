"""Backtest barra a barra, só comprado, com taxas, slippage e stop com trailing.

Ordem dos eventos em cada barra i:
1. Na abertura, executa a ordem gerada pelo sinal do fechamento de i-1.
2. Durante a barra, se a mínima tocar o stop, sai no stop (ou na abertura, se abriu abaixo dele).
3. No fechamento, marca o patrimônio, sobe o trailing stop e avalia os sinais para i+1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from trader.risk import RiskConfig, position_size
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
    return {
        "total_return": float(total),
        "cagr": float(cagr),
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


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    *,
    initial_cash: float = 10_000.0,
    costs: CostModel | None = None,
    risk: RiskConfig | None = None,
    trade_from: pd.Timestamp | None = None,
) -> BacktestResult:
    """Roda a estratégia em um ativo. `trade_from` limita as operações (e a curva) a partir dessa data,
    usando as barras anteriores só como aquecimento dos indicadores."""
    costs = costs or CostModel()
    risk = risk or RiskConfig()
    sig = strategy.generate(df)
    idx = sig.index
    o, lo, c = (sig[k].to_numpy(float) for k in ("open", "low", "close"))
    atr_ = sig["atr"].to_numpy(float)
    entry, exit_ = sig["entry"].to_numpy(bool), sig["exit"].to_numpy(bool)
    n = len(sig)

    start = strategy.warmup
    if trade_from is not None:
        start = max(start, int(idx.searchsorted(trade_from)))
    equity = np.full(n, np.nan)
    trades: list[Trade] = []
    if start >= n:
        return BacktestResult(strategy.name, strategy.params(), pd.Series(equity, idx).dropna(), [])

    cash, qty, stop, cost_basis = initial_cash, 0.0, np.nan, 0.0
    entry_px, entry_t = 0.0, idx[start]
    pending: str | None = None
    bars_in = 0

    def close_position(i: int, fill: float, reason: str) -> None:
        nonlocal cash, qty, stop
        proceeds = qty * fill * (1 - costs.fee_rate)
        pnl = proceeds - cost_basis
        trades.append(Trade(entry_t, idx[i], entry_px, fill, qty, pnl, pnl / cost_basis, reason))
        cash += proceeds
        qty, stop = 0.0, np.nan

    for i in range(start, n):
        if pending == "sell" and qty > 0:
            close_position(i, o[i] * (1 - costs.slippage), "signal")
        elif pending == "buy" and qty == 0 and not np.isnan(atr_[i - 1]):
            fill = o[i] * (1 + costs.slippage)
            stop_px = fill - strategy.stop_atr_mult * atr_[i - 1]
            q = position_size(cash, fill, stop_px, cash, risk, costs.fee_rate)
            if q > 0:
                cost_basis = q * fill * (1 + costs.fee_rate)
                cash -= cost_basis
                qty, stop, entry_px, entry_t = q, stop_px, fill, idx[i]
        pending = None

        if qty > 0 and lo[i] <= stop:
            close_position(i, min(o[i], stop) * (1 - costs.slippage), "stop")

        if qty > 0:
            bars_in += 1
            stop = max(stop, c[i] - strategy.stop_atr_mult * atr_[i])
        equity[i] = cash + qty * c[i]

        if qty > 0 and exit_[i]:
            pending = "sell"
        elif qty == 0 and entry[i]:
            pending = "buy"

    if qty > 0:
        close_position(n - 1, c[-1] * (1 - costs.slippage), "end")
        equity[n - 1] = cash

    eq = pd.Series(equity, idx).dropna()
    result = BacktestResult(strategy.name, strategy.params(), eq, trades)
    result.metrics = compute_metrics(eq, trades, bars_in / max(1, n - start), sig["close"])
    return result
