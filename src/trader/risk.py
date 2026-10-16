"""Regras de risco: tamanho de posição por risco fixo e limites do agente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01  # fração do patrimônio perdida se o stop for atingido
    max_position_pct: float = 0.30  # teto de uma posição em fração do patrimônio
    max_open_positions: int = 3
    max_drawdown: float = 0.20  # kill switch do agente: para de abrir posições
    min_notional: float = 10.0  # valor mínimo de ordem na moeda de cotação


def position_size(
    equity: float,
    entry_price: float,
    stop_price: float,
    cash: float,
    cfg: RiskConfig,
    fee_rate: float = 0.0,
) -> float:
    """Quantidade a comprar para perder no máximo `risk_per_trade` do patrimônio no stop."""
    if entry_price <= 0 or stop_price >= entry_price:
        return 0.0
    qty = equity * cfg.risk_per_trade / (entry_price - stop_price)
    qty = min(
        qty,
        equity * cfg.max_position_pct / entry_price,
        cash / (entry_price * (1 + fee_rate)),
    )
    if qty * entry_price < cfg.min_notional:
        return 0.0
    return qty


def drawdown(equity: float, peak: float) -> float:
    return 0.0 if peak <= 0 else max(0.0, 1 - equity / peak)
