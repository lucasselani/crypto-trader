"""Contrato das estratégias.

Uma estratégia recebe candles fechados e devolve, por barra, se há sinal de entrada e de saída.
O sinal da barra t usa só dados até o fechamento de t; quem executa (backtest ou agente) age na
abertura de t+1. O stop é sempre ATR * `stop_atr_mult` abaixo do preço, com trailing pelo
fechamento.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, replace
from typing import Any, ClassVar

import pandas as pd

from trader.indicators import atr


@dataclass(frozen=True)
class Strategy(ABC):
    stop_atr_mult: float = 3.0
    atr_period: int = 14
    # Filtro de euforia: não entra se a média recente do funding (coluna `funding`, ver
    # data.attach_funding) passar deste valor. None desliga; sem dado de funding, não bloqueia.
    max_funding: float | None = None

    name: ClassVar[str] = ""
    # Grade de parâmetros usada no walk-forward
    grid: ClassVar[dict[str, list[Any]]] = {}

    @property
    @abstractmethod
    def warmup(self) -> int:
        """Barras necessárias antes de o primeiro sinal ser válido."""

    @abstractmethod
    def signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """Retorna (entry, exit) como séries booleanas alinhadas a `df`."""

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["atr"] = atr(df, self.atr_period)
        entry, exit_ = self.signals(df)
        if self.max_funding is not None and "funding" in df:
            entry = entry & ~(df["funding"] > self.max_funding)
        out["entry"] = entry.fillna(False).astype(bool)
        out["exit"] = exit_.fillna(False).astype(bool)
        warm = min(self.warmup, len(out))
        out.iloc[:warm, out.columns.get_indexer(["entry", "exit"])] = False
        return out

    def params(self) -> dict[str, Any]:
        return asdict(self)

    def with_params(self, **params: Any) -> Strategy:
        return replace(self, **params)
