import numpy as np
import pandas as pd

from trader.regimes import label_regimes, regime_mix, regime_stats


def _series(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D", tz="UTC"))


def test_labels_use_only_the_past():
    close = _series(np.r_[np.full(10, 100.0), np.full(10, 150.0), np.full(10, 90.0)])
    lab = label_regimes(close, window=5, bull=0.2, bear=-0.2)
    assert lab.iloc[:5].isna().all()
    assert lab.iloc[9] == "lateral"
    assert lab.iloc[12] == "alta"  # 150 vs 100 de 5 dias antes
    assert lab.iloc[22] == "baixa"  # 90 vs 150
    assert lab.iloc[29] == "lateral"


def test_regime_stats_attributes_returns_to_previous_label():
    labels = _series(["alta"] * 5 + ["baixa"] * 5)
    equity = _series([100, 101, 102, 103, 104, 105, 100, 95, 90, 85])
    st = regime_stats(equity, labels)
    assert st.loc["alta", "dias"] == 5  # dias 1-4 (rótulo de 0-3) + dia 5 (rótulo do dia 4)
    assert st.loc["alta", "mensal"] > 0 and st.loc["baixa", "mensal"] < 0
    assert st.loc["lateral", "dias"] == 0
    assert st.loc["baixa", "pior_queda"] < -0.1


def test_regime_mix_sums_to_one():
    labels = _series(["alta", "lateral", "lateral", "baixa"])
    mix = regime_mix(labels)
    assert abs(mix.sum() - 1) < 1e-12 and mix["lateral"] == 0.5
