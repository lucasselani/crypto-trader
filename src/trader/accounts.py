"""Contas de paper congeladas: várias estratégias rodando em paralelo, cada uma com saldo próprio.

O arquivo de contas (JSON versionado) guarda a data de congelamento e os parâmetros de cada conta.
Assim dá para medir depois, sem trapaça, como cada estratégia se saiu nos meses seguintes
(`trader forward`), e comparar com o que o paper de fato fez (`trader status`).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import pandas as pd

from trader.config import Settings
from trader.strategies import Strategy, get_strategy


@dataclass
class Account:
    name: str
    strategy: str
    timeframe: str
    params: dict = field(default_factory=dict)
    risk_per_trade: float = 0.01
    max_open_positions: int = 3

    def build(self) -> Strategy:
        return get_strategy(self.strategy, **self.params)

    def settings(self, base: Settings) -> Settings:
        return replace(
            base,
            mode="paper",
            timeframe=self.timeframe,
            strategy=self.strategy,
            symbols=list(base.universe),
            risk=replace(base.risk, risk_per_trade=self.risk_per_trade,
                         max_open_positions=self.max_open_positions),
            state_dir=base.state_dir / "accounts" / self.name,
        )


@dataclass
class AccountBook:
    frozen_at: str
    accounts: list[Account]

    @classmethod
    def load(cls, path: Path) -> AccountBook:
        raw = json.loads(Path(path).read_text())
        return cls(raw["frozen_at"], [Account(**a) for a in raw["accounts"]])

    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(
            {"frozen_at": self.frozen_at, "accounts": [asdict(a) for a in self.accounts]},
            indent=2, ensure_ascii=False) + "\n")

    @property
    def frozen_ts(self) -> pd.Timestamp:
        return pd.Timestamp(self.frozen_at, tz="UTC")
