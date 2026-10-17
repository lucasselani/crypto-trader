"""Rotação: a cada `rebalance` barras, ranqueia os ativos por uma nota e fica com os `top_k` melhores.

Diferente das outras estratégias, que decidem ativo por ativo, aqui os ativos competem entre si.
Só entram ativos elegíveis (preço acima da média de regime) com nota acima de `min_score`; se não
houver nenhum, fica em caixa. Entre um rebalanceamento e outro, sai antes se o ativo perder a
elegibilidade ou bater no stop. Ideias dos fatores acadêmicos do zoo do Vibe-Trading (MIT).
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd

from trader.indicators import sma
from trader.strategies.base import Strategy


@dataclass(frozen=True)
class RotationStrategy(Strategy):
    top_k: int = 3
    rebalance: int = 7  # em barras (7 no diário = semanal)
    regime: int = 200
    stop_atr_mult: float = 4.0
    exposure: float = 1.0  # fração do patrimônio dividida entre as top_k fatias; o resto fica em caixa

    min_score: ClassVar[float] = -np.inf

    @abstractmethod
    def score(self, df: pd.DataFrame) -> pd.Series:
        """Nota de cada barra; maior = mais forte. Só pode usar dados até a barra."""

    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        eligible = df["close"] > sma(df["close"], self.regime)
        return eligible, ~eligible

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        out = super().generate(df)
        score = self.score(df).astype(float)
        score.iloc[: min(self.warmup, len(score))] = np.nan
        out["score"] = score
        return out


@dataclass(frozen=True)
class MomentumRotation(RotationStrategy):
    """Fica com as moedas que mais subiram nos últimos `lookback` barras (momentum entre ativos,
    Carhart 1997). Só compra com retorno positivo (momentum absoluto)."""

    lookback: int = 60

    name: ClassVar[str] = "momentum_rotation"
    min_score: ClassVar[float] = 0.0
    grid: ClassVar[dict[str, list]] = {
        "lookback": [30, 60, 90, 180],
        "top_k": [2, 3],
        "regime": [100, 200],
        "stop_atr_mult": [3.0, 5.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.lookback, self.regime, self.atr_period) + 1

    def score(self, df: pd.DataFrame) -> pd.Series:
        return df["close"] / df["close"].shift(self.lookback) - 1


@dataclass(frozen=True)
class High52wRotation(RotationStrategy):
    """Fica com as moedas mais próximas da própria máxima de `n` barras (George & Hwang 2004)."""

    n: int = 365

    name: ClassVar[str] = "high52w_rotation"
    grid: ClassVar[dict[str, list]] = {
        "n": [180, 365],
        "top_k": [2, 3],
        "regime": [100, 200],
        "stop_atr_mult": [3.0, 5.0],
    }

    @property
    def warmup(self) -> int:
        return max(self.n, self.regime, self.atr_period) + 1

    def score(self, df: pd.DataFrame) -> pd.Series:
        return df["close"] / df["close"].rolling(self.n, min_periods=self.n).max()
