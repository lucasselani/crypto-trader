import numpy as np
import pandas as pd

from tests.conftest import make_candles
from trader.indicators import atr, donchian_high, donchian_low, ema, rsi, sma


def test_sma_and_ema_basic():
    s = pd.Series([1.0, 2, 3, 4, 5])
    assert sma(s, 3).tolist()[2:] == [2.0, 3.0, 4.0]
    assert np.isnan(ema(s, 3).iloc[1])
    assert ema(pd.Series([5.0] * 10), 3).iloc[-1] == 5.0


def test_rsi_extremes():
    assert rsi(pd.Series(np.arange(1.0, 40.0)), 14).iloc[-1] == 100.0
    assert rsi(pd.Series(np.arange(40.0, 1.0, -1)), 14).iloc[-1] < 1.0


def test_atr_constant_range():
    df = make_candles([100.0] * 30, spread=0.01)
    assert abs(atr(df, 14).iloc[-1] - 2.0) < 1e-9  # high 101, low 99


def test_donchian_excludes_current_bar():
    s = pd.Series([1.0, 2, 3, 10])
    assert donchian_high(s, 3).iloc[-1] == 3.0
    assert donchian_low(s, 3).iloc[-1] == 1.0
