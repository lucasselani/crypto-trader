"""Diário de decisões do agente em JSONL (uma linha por decisão, inclusive 'não fazer nada')."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class Decision:
    symbol: str
    action: str  # buy | sell | stop | trail | hold | skip
    reason: str
    bar_time: str = ""
    price: float | None = None
    qty: float | None = None
    stop: float | None = None
    mode: str = ""
    logged_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def append(path: Path, decisions: list[Decision]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(asdict(d), ensure_ascii=False) + "\n")
