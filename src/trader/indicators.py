"""Indicadores técnicos. Todos usam só dados até a barra corrente (sem olhar o futuro)."""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n, min_periods=n).mean()


def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    """RSI de Wilder."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    out = 100 - 100 / (1 + avg_gain / avg_loss)
    return out.mask(avg_loss == 0, 100.0)


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    ranges = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ATR de Wilder."""
    return true_range(df).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def donchian_high(high: pd.Series, n: int) -> pd.Series:
    """Máxima das n barras anteriores (exclui a barra corrente)."""
    return high.rolling(n, min_periods=n).max().shift(1)


def donchian_low(low: pd.Series, n: int) -> pd.Series:
    """Mínima das n barras anteriores (exclui a barra corrente)."""
    return low.rolling(n, min_periods=n).min().shift(1)
