from trader.strategies.base import Strategy
from trader.strategies.trend import DonchianBreakout, EmaCross, RsiPullback

STRATEGIES: dict[str, type[Strategy]] = {
    cls.name: cls for cls in (EmaCross, DonchianBreakout, RsiPullback)
}


def get_strategy(name: str, **params) -> Strategy:
    try:
        cls = STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Estratégia desconhecida: {name!r} (disponíveis: {', '.join(STRATEGIES)})")
    return cls(**params)


__all__ = ["STRATEGIES", "DonchianBreakout", "EmaCross", "RsiPullback", "Strategy", "get_strategy"]
