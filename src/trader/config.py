"""Configuração lida do ambiente (.env). O modo live só liga com dupla confirmação."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from trader.backtest import CostModel
from trader.risk import RiskConfig

MODES = ("paper", "testnet", "live")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    exchange: str = "binance"
    mode: str = "paper"
    allow_live: bool = False
    api_key: str | None = None
    api_secret: str | None = None
    symbols: list[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe: str = "1d"
    strategy: str = "donchian"
    risk: RiskConfig = field(default_factory=RiskConfig)
    costs: CostModel = field(default_factory=CostModel)
    paper_cash: float = 10_000.0
    data_dir: Path = Path("data")
    state_dir: Path = Path("state")

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        mode = _env("TRADER_MODE", "paper")
        if mode not in MODES:
            raise ValueError(f"TRADER_MODE inválido: {mode!r} (use {', '.join(MODES)})")
        return cls(
            exchange=_env("TRADER_EXCHANGE", "binance"),
            mode=mode,
            allow_live=_env("TRADER_ALLOW_LIVE", "no").lower() == "yes",
            api_key=_env("TRADER_API_KEY", "") or None,
            api_secret=_env("TRADER_API_SECRET", "") or None,
            symbols=[s.strip() for s in _env("TRADER_SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",") if s.strip()],
            timeframe=_env("TRADER_TIMEFRAME", "1d"),
            strategy=_env("TRADER_STRATEGY", "donchian"),
            risk=RiskConfig(
                risk_per_trade=float(_env("TRADER_RISK_PER_TRADE", "0.01")),
                max_position_pct=float(_env("TRADER_MAX_POSITION_PCT", "0.30")),
                max_open_positions=int(_env("TRADER_MAX_OPEN_POSITIONS", "3")),
                max_drawdown=float(_env("TRADER_MAX_DRAWDOWN", "0.20")),
            ),
            costs=CostModel(
                fee_rate=float(_env("TRADER_FEE_RATE", "0.001")),
                slippage=float(_env("TRADER_SLIPPAGE", "0.0005")),
            ),
            paper_cash=float(_env("TRADER_PAPER_CASH", "10000")),
            data_dir=Path(_env("TRADER_DATA_DIR", "data")),
            state_dir=Path(_env("TRADER_STATE_DIR", "state")),
        )

    def check_live_allowed(self) -> None:
        if self.mode == "live" and not self.allow_live:
            raise RuntimeError(
                "Modo live bloqueado: defina TRADER_ALLOW_LIVE=yes conscientemente antes de operar real."
            )
