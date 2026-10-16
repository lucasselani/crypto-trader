from trader.risk import RiskConfig, drawdown, position_size


def test_position_risks_fixed_fraction():
    cfg = RiskConfig(risk_per_trade=0.01, max_position_pct=1.0)
    qty = position_size(10_000, 100, 90, 10_000, cfg)
    assert abs(qty * (100 - 90) - 100) < 1e-9


def test_position_capped_by_max_pct_and_cash():
    cfg = RiskConfig(risk_per_trade=0.05, max_position_pct=0.30)
    assert abs(position_size(10_000, 100, 99, 10_000, cfg) * 100 - 3_000) < 1e-9
    assert abs(position_size(10_000, 100, 99, 500, cfg) * 100 - 500) < 1e-9


def test_invalid_stop_and_min_notional():
    cfg = RiskConfig()
    assert position_size(10_000, 100, 100, 10_000, cfg) == 0
    assert position_size(100, 100, 50, 100, cfg) == 0  # 2 USDT < mínimo


def test_drawdown():
    assert abs(drawdown(80, 100) - 0.2) < 1e-12
    assert drawdown(120, 100) == 0.0
