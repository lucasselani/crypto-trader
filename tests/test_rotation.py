import numpy as np

from tests.conftest import make_candles
from trader.backtest import CostModel, run_portfolio
from trader.risk import RiskConfig
from trader.strategies import MomentumRotation

NO_COSTS = CostModel(0.0, 0.0)
STRAT = MomentumRotation(lookback=10, regime=20, top_k=1, rebalance=5, stop_atr_mult=50.0)


def test_holds_the_strongest_asset():
    n = 120
    data = {
        "UP": make_candles(100 * np.exp(np.linspace(0, 0.8, n))),
        "SLOW": make_candles(100 * np.exp(np.linspace(0, 0.2, n))),
        "DOWN": make_candles(100 * np.exp(np.linspace(0, -0.5, n))),
    }
    res = run_portfolio(data, STRAT, costs=NO_COSTS, risk=RiskConfig())
    assert {t.symbol for t in res.trades} == {"UP"}
    assert res.equity.iloc[-1] > 10_000


def test_rotates_when_leadership_changes():
    first = np.r_[np.linspace(0, 0.6, 80), np.full(80, 0.6)]
    second = np.r_[np.full(80, 0.0), np.linspace(0, 0.6, 80)]
    data = {"A": make_candles(100 * np.exp(first)), "B": make_candles(100 * np.exp(second))}
    res = run_portfolio(data, STRAT, costs=NO_COSTS, risk=RiskConfig())
    symbols = [t.symbol for t in res.trades]
    assert symbols[0] == "A" and "B" in symbols


def test_stays_in_cash_without_positive_momentum():
    n = 120
    data = {s: make_candles(100 * np.exp(np.linspace(0, -0.4, n))) for s in ("X", "Y")}
    res = run_portfolio(data, STRAT, costs=NO_COSTS, risk=RiskConfig())
    assert res.trades == [] and res.equity.iloc[-1] == 10_000


def test_slots_split_equity():
    n = 120
    data = {s: make_candles(100 * np.exp(np.linspace(0, g, n)))
            for s, g in (("A", 0.8), ("B", 0.6), ("C", 0.4))}
    strat = MomentumRotation(lookback=10, regime=20, top_k=3, rebalance=5, stop_atr_mult=50.0)
    res = run_portfolio(data, strat, costs=NO_COSTS, risk=RiskConfig())
    first = sorted(res.trades, key=lambda t: t.entry_time)[:3]
    sizes = [t.qty * t.entry_price for t in first]
    assert len({t.symbol for t in first}) == 3
    assert max(sizes) - min(sizes) < 1.0  # ~1/3 do patrimônio cada
