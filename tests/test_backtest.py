from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd

from tests.conftest import make_candles
from trader.backtest import CostModel, run_backtest
from trader.risk import RiskConfig
from trader.strategies import STRATEGIES, Strategy

ALL_IN = RiskConfig(risk_per_trade=1.0, max_position_pct=1.0)
NO_COSTS = CostModel(0.0, 0.0)


@dataclass(frozen=True)
class Scripted(Strategy):
    """Estratégia de teste: entra/sai em barras fixas."""

    entries: tuple = ()
    exits: tuple = ()
    stop_atr_mult: float = 50.0
    atr_period: int = 2
    name: ClassVar[str] = "scripted"

    @property
    def warmup(self) -> int:
        return 3

    def signals(self, df):
        e = pd.Series(False, index=df.index)
        x = pd.Series(False, index=df.index)
        e.iloc[list(self.entries)] = True
        x.iloc[list(self.exits)] = True
        return e, x


def test_signal_executes_on_next_open():
    df = make_candles([100, 100, 100, 100, 110, 120, 130, 140, 150, 160])
    res = run_backtest(df, Scripted(entries=(4,), exits=(7,)), costs=NO_COSTS, risk=ALL_IN)
    t = res.trades[0]
    assert t.entry_time == df.index[5] and t.entry_price == df["open"].iloc[5]
    assert t.exit_time == df.index[8] and t.exit_price == df["open"].iloc[8]
    assert t.reason == "signal"


def test_fees_and_slippage_reduce_pnl():
    df = make_candles([100, 100, 100, 100, 110, 120, 130, 140, 150, 160])
    strat = Scripted(entries=(4,), exits=(7,))
    free = run_backtest(df, strat, costs=NO_COSTS, risk=ALL_IN).trades[0].pnl
    paid = run_backtest(df, strat, costs=CostModel(0.001, 0.001), risk=ALL_IN).trades[0].pnl
    assert paid < free


def test_flat_market_with_costs_loses_money():
    df = make_candles([100.0] * 12)
    res = run_backtest(df, Scripted(entries=(3,), exits=(5,)), costs=CostModel(0.001, 0.0),
                       risk=ALL_IN)
    assert res.equity.iloc[-1] < 10_000


def test_stop_gap_down_fills_at_open():
    closes = [100, 100, 100, 100, 100, 100, 50, 50]
    df = make_candles(closes, spread=0.01)
    df.iloc[6, df.columns.get_loc("open")] = 50.0  # abre em gap abaixo do stop
    res = run_backtest(df, Scripted(entries=(4,), stop_atr_mult=1.0), costs=NO_COSTS, risk=ALL_IN)
    t = res.trades[0]
    assert t.reason == "stop" and t.exit_price == 50.0


def test_trade_from_limits_trading_window(random_walk):
    cut = random_walk.index[1000]
    for cls in STRATEGIES.values():
        res = run_backtest(random_walk, cls(), trade_from=cut)
        assert res.equity.index[0] >= cut
        assert all(t.entry_time >= cut for t in res.trades)


def test_no_lookahead(random_walk):
    """Mudar o futuro não pode mudar operações já abertas antes dele."""
    for cls in STRATEGIES.values():
        strat = cls()
        cut = 1200
        full = run_backtest(random_walk, strat).trades
        altered = random_walk.copy()
        altered.iloc[cut:] *= 0.5
        alt = run_backtest(altered, strat).trades
        before = [t.entry_time for t in full if t.exit_time < random_walk.index[cut - 1]]
        assert before == [t.entry_time for t in alt if t.exit_time < random_walk.index[cut - 1]]


def test_metrics_are_finite(random_walk):
    for cls in STRATEGIES.values():
        m = run_backtest(random_walk, cls()).metrics
        assert np.isfinite(m["total_return"]) and -1 <= m["max_drawdown"] <= 0
        assert 0 <= m["exposure"] <= 1
