from backend.services.dynamic_compounding import DynamicCompoundingConfig, build_dynamic_compounding


def _trade(date: str, pnl: float) -> dict:
    return {"trade_date2": date, "net_profit": pnl}


def test_dynamic_compounding_drawdown_switch_and_mdd():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=10.0,
        add_ratio=1.0,
        rollback_amount=20.0,
        max_multiple=2.0,
    )
    trades = [
        _trade("2024-01-10", 30.0),
        _trade("2024-02-10", 10.0),
        _trade("2024-03-10", -40.0),
        _trade("2024-04-10", 50.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    monthly = out["monthly"]
    assert abs(monthly["final_net_value"] - 94.875) < 1e-6
    assert abs(monthly["mdd_amount"] - 50.6) < 1e-6
    assert monthly["rollback_adjust_count"] == 1
    assert monthly["reach_10x_date"] == "未達成"


def test_dynamic_compounding_recovery_switch_back_to_add_ratio():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=10.0,
        add_ratio=1.0,
        rollback_amount=20.0,
        max_multiple=2.0,
    )
    trades = [
        _trade("2024-01-10", 30.0),
        _trade("2024-02-10", 10.0),
        _trade("2024-03-10", -40.0),
        _trade("2024-04-10", 150.0),
        _trade("2024-05-10", 10.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    monthly = out["monthly"]
    assert abs(monthly["final_net_value"] - 146.1075) < 1e-6


def test_dynamic_compounding_cap_enforced():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=2.0,
        add_threshold_profit=9999.0,
        add_ratio=2.0,
        rollback_amount=9999.0,
        max_multiple=1.5,
    )
    trades = [_trade("2024-01-10", 100.0)]
    out = build_dynamic_compounding(trades, cfg)
    monthly = out["monthly"]
    assert abs(monthly["final_net_value"] - 250.0) < 1e-6


def test_dynamic_compounding_reach_10x_date():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=1.0,
        add_threshold_profit=9999.0,
        add_ratio=1.0,
        rollback_amount=9999.0,
        max_multiple=20.0,
    )
    trades = [
        _trade("2024-01-10", 500.0),
        _trade("2024-02-10", 500.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    monthly = out["monthly"]
    assert monthly["reach_10x_date"] == "2024-02-10"
