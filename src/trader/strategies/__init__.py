from trader.strategies.base import Strategy
from trader.strategies.rotation import High52wRotation, MomentumRotation, RotationStrategy
from trader.strategies.trend import (
    DonchianBreakout,
    EmaCross,
    KeltnerBreakout,
    RocMomentum,
    RsiPullback,
    SmaTrend,
)

STRATEGIES: dict[str, type[Strategy]] = {
    cls.name: cls
    for cls in (EmaCross, DonchianBreakout, RsiPullback, SmaTrend, RocMomentum, KeltnerBreakout,
                MomentumRotation, High52wRotation)
}


def get_strategy(name: str, **params) -> Strategy:
    try:
        cls = STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Estratégia desconhecida: {name!r} (disponíveis: {', '.join(STRATEGIES)})")
    return cls(**params)


__all__ = [
    "STRATEGIES", "DonchianBreakout", "EmaCross", "High52wRotation", "KeltnerBreakout",
    "MomentumRotation", "RocMomentum", "RotationStrategy", "RsiPullback", "SmaTrend", "Strategy",
    "get_strategy",
]
