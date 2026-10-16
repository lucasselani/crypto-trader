from trader.strategies import DonchianBreakout
from trader.walkforward import param_grid, walk_forward


def test_param_grid():
    assert len(param_grid({"a": [1, 2], "b": [3, 4, 5]})) == 6


def test_walk_forward_windows_are_out_of_sample(random_walk):
    res = walk_forward(random_walk, DonchianBreakout(), train_bars=400, test_bars=200,
                       grid={"entry_n": [20, 40], "stop_atr_mult": [2.0, 3.0]})
    assert len(res.windows) == 6
    for w in res.windows:
        assert w.train_start < w.test_start
        assert set(w.params) == {"entry_n", "stop_atr_mult"}
    assert res.equity.index[0] >= random_walk.index[400]
    assert res.equity.index.is_monotonic_increasing
