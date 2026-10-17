"""Estratégias de tendência e de pullback, só compradas (spot)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd

from trader.indicators import atr, donchian_high, donchian_low, ema, roc, rsi, sma
from trader.strategies.base import Strategy


@dataclass(frozen=True)
class EmaCross(Strategy):
    """Compra quando a média rápida cruza a lenta para cima, com o preço acima da média de regime."""

    fast: int = 20
    slow: int = 50
    regime: int = 200

    name: ClassVar[str] = "ema_cross"
    grid: ClassVar[dict[str, list]] = {
        "fast": [10, 20, 30],
        "slow": [50, 100],
        "regime": [150, 200],
        "stop_atr_mult": [2.0, 3.0, 4.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.fast, self.slow, self.regime, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        fast, slow, regime = ema(close, self.fast), ema(close, self.slow), sma(close, self.regime)
        above = fast > slow
        cross_up = above & ~above.shift(1, fill_value=False)
        return cross_up & (close > regime), fast < slow


@dataclass(frozen=True)
class DonchianBreakout(Strategy):
    """Rompimento de canal (estilo Turtle): compra na máxima de N barras, sai na mínima de M."""

    entry_n: int = 20
    exit_n: int = 10
    regime: int = 200

    name: ClassVar[str] = "donchian"
    grid: ClassVar[dict[str, list]] = {
        "entry_n": [20, 40, 55],
        "exit_n": [10, 20],
        "regime": [150, 200],
        "stop_atr_mult": [2.0, 3.0, 4.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.entry_n, self.exit_n, self.regime, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        entry = (close > donchian_high(df["high"], self.entry_n)) & (close > sma(close, self.regime))
        exit_ = close < donchian_low(df["low"], self.exit_n)
        return entry, exit_


@dataclass(frozen=True)
class RsiPullback(Strategy):
    """Compra correção (RSI baixo) dentro de tendência de alta; vende quando o RSI se recupera."""

    rsi_n: int = 14
    entry_below: float = 35.0
    exit_above: float = 55.0
    regime: int = 200

    name: ClassVar[str] = "rsi_pullback"
    grid: ClassVar[dict[str, list]] = {
        "rsi_n": [7, 14],
        "entry_below": [30.0, 35.0, 40.0],
        "exit_above": [50.0, 60.0],
        "stop_atr_mult": [2.0, 3.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.rsi_n, self.regime, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        r = rsi(close, self.rsi_n)
        return (r < self.entry_below) & (close > sma(close, self.regime)), r > self.exit_above


@dataclass(frozen=True)
class SmaTrend(Strategy):
    """Filtro de tendência puro (estilo Meb Faber): compra quando o preço cruza a média para cima,
    sai quando fecha abaixo dela."""

    n: int = 150
    stop_atr_mult: float = 4.0

    name: ClassVar[str] = "sma_trend"
    grid: ClassVar[dict[str, list]] = {
        "n": [50, 100, 150, 200],
        "stop_atr_mult": [3.0, 4.0, 5.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.n, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        above = close > sma(close, self.n)
        return above & ~above.shift(1, fill_value=False), ~above


@dataclass(frozen=True)
class RocMomentum(Strategy):
    """Momentum em série temporal: compra quando a variação de N barras vira positiva (com o preço
    acima da média de regime), sai quando ela fica negativa."""

    lookback: int = 60
    regime: int = 200

    name: ClassVar[str] = "roc_momentum"
    grid: ClassVar[dict[str, list]] = {
        "lookback": [30, 60, 90],
        "regime": [100, 200],
        "stop_atr_mult": [3.0, 4.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.lookback, self.regime, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        positive = roc(close, self.lookback) > 0
        turned = positive & ~positive.shift(1, fill_value=False)
        return turned & (close > sma(close, self.regime)), ~positive


@dataclass(frozen=True)
class KeltnerBreakout(Strategy):
    """Rompimento de volatilidade: compra quando fecha acima de média + k × ATR (com o preço acima da
    média de regime), sai quando volta para baixo da média."""

    n: int = 20
    k: float = 2.0
    regime: int = 200

    name: ClassVar[str] = "keltner"
    grid: ClassVar[dict[str, list]] = {
        "n": [20, 50],
        "k": [1.5, 2.0, 2.5],
        "stop_atr_mult": [2.0, 3.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.n, self.regime, self.atr_period) + 1

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        close = df["close"]
        mid = ema(close, self.n)
        upper = mid + self.k * atr(df, self.n)
        return (close > upper) & (close > sma(close, self.regime)), close < mid
