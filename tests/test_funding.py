import numpy as np
import pandas as pd

from tests.conftest import make_candles
from trader.data import attach_funding
from trader.strategies import EmaCross


def test_attach_funding_uses_only_payments_known_at_close():
    candles = make_candles([100.0] * 3)  # abre 01/01, 02/01, 03/01
    t0 = pd.Timestamp("2020-01-01", tz="UTC")
    funding = pd.Series([0.1, 0.2, 0.3, 0.4], index=[
        t0 + pd.Timedelta(hours=8), t0 + pd.Timedelta(hours=16),
        t0 + pd.Timedelta(days=1, hours=8), t0 + pd.Timedelta(days=3)])
    out = attach_funding(candles, funding, timeframe_s=86400, window=1)
    assert out["funding"].tolist()[:2] == [0.2, 0.3]  # o de 00:00 de 02/01 não é do candle de 01/01
    assert out["funding"].iloc[2] == 0.3  # pagamento de 04/01 00:00 ainda não existia


def test_funding_filter_blocks_entries_and_nan_passes(random_walk):
    base = EmaCross()
    entries = base.generate(random_walk)["entry"]
    hot = random_walk.assign(funding=1.0)
    assert not EmaCross(max_funding=0.001).generate(hot)["entry"].any()
    unknown = random_walk.assign(funding=np.nan)
    assert (EmaCross(max_funding=0.001).generate(unknown)["entry"] == entries).all()
    assert (EmaCross().generate(hot)["entry"] == entries).all()  # filtro desligado


def test_funding_cache_roundtrip_keeps_datetimes(tmp_path):
    from trader.data import load_funding

    idx = pd.to_datetime(["2020-01-01 00:00:00", "2020-01-01 08:00:00.001"], utc=True,
                         format="ISO8601")
    s = pd.Series([0.0001, 0.0002], index=idx, name="funding")
    s.index.name = "time"
    s.to_frame().to_csv(tmp_path / "funding_binanceusdm_BTC-USDT.csv", index_label="time")
    loaded = load_funding("BTC/USDT", data_dir=tmp_path, refresh=False)
    assert isinstance(loaded.index, pd.DatetimeIndex) and loaded.index.tz is not None
    out = attach_funding(make_candles([1.0, 1.0]), loaded, 86400, window=1)
    assert out["funding"].iloc[0] == 0.0002
