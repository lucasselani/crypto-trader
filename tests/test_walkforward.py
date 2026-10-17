from trader.strategies import DonchianBreakout
from trader.walkforward import evaluate, param_grid, walk_forward


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


def test_walk_forward_portfolio_and_criteria(random_walk):
    late = random_walk.iloc[600:] * 1.5
    res = walk_forward({"A": random_walk, "B": late}, DonchianBreakout(), train_bars=400,
                       test_bars=200, grid={"entry_n": [20, 40]})
    assert len(res.windows) == 6
    checks = evaluate(res)
    assert set(checks) == {"calmar", "profit_factor", "trades", "positive_windows", "drawdown",
                           "approved"}
    assert checks["approved"] == all(v for k, v in checks.items() if k != "approved")


def test_criteria_thresholds():
    import pandas as pd

    from trader.walkforward import Criteria, WalkForwardResult, Window

    t = pd.Timestamp("2024-01-01", tz="UTC")
    win = Window(t, t, t, {}, {}, {"trades": 5, "total_return": 0.1})
    good = WalkForwardResult("x", [win], pd.Series(dtype=float),
                             {"calmar": 1.5, "profit_factor": 2.0, "trades": 40,
                              "max_drawdown": -0.2})
    assert evaluate(good)["approved"]
    assert not evaluate(good, Criteria(min_trades=50))["approved"]
    good.metrics["max_drawdown"] = -0.5
    assert not evaluate(good)["approved"]
