import numpy as np
import pandas as pd
import pytest


def make_candles(closes, start="2020-01-01", freq="1D", spread=0.01) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    idx = pd.date_range(start, periods=len(closes), freq=freq, tz="UTC", name="time")
    return pd.DataFrame({
        "open": opens,
        "high": np.maximum(opens, closes) * (1 + spread),
        "low": np.minimum(opens, closes) * (1 - spread),
        "close": closes,
        "volume": 1.0,
    }, index=idx)


@pytest.fixture
def random_walk() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    closes = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.03, 1500)))
    return make_candles(closes)
