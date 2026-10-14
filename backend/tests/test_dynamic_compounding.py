from datetime import datetime

import io
import json
import zipfile

from backend.services.dynamic_compounding import (
    DynamicCompoundingConfig,
    build_dynamic_compounding,
    build_dynamic_compounding_report,
)
from backend.services.dynamic_compounding_report import serialize_dynamic_compounding_sea
from backend.services.parser import parse_file


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
    assert abs(monthly["final_net_value"] - 105.0) < 1e-6
    assert abs(monthly["mdd_amount"] - 80.0) < 1e-6
    assert monthly["mdd_amount_date"] == "2024-03-10"
    assert monthly["mdd_pct_date"] == "2024-03-10"
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
    assert abs(monthly["final_net_value"] - 195.0) < 1e-6


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
    assert abs(monthly["final_net_value"] - 200.0) < 1e-6


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


def test_dynamic_compounding_curve_is_weekly_sampled_but_mdd_is_intratrade():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=1.0,
        add_threshold_profit=9999.0,
        add_ratio=1.0,
        rollback_amount=9999.0,
        max_multiple=99.0,
    )
    trades = [
        _trade("2024-01-02", 100.0),
        _trade("2024-01-03", -100.0),
        _trade("2024-01-12", 20.0),
        _trade("2024-01-19", -10.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    weekly = out["weekly"]
    monthly = out["monthly"]
    assert [p["date"] for p in weekly["curve"]] == [p["date"] for p in monthly["curve"]]
    # The curve stays weekly, but same-week highs and lows are included in MDD.
    for result in (weekly, monthly):
        assert abs(result["mdd_amount"] - 100.0) < 1e-6
        assert abs(result["mdd_pct"] - 50.0) < 1e-6
        assert result["mdd_amount_date"] == "2024-01-03"
        assert result["mdd_pct_date"] == "2024-01-03"


def test_dynamic_compounding_rollback_percent_trigger():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=10.0,
        add_ratio=1.0,
        rollback_amount=9_999.0,
        rollback_percent=0.1,
        max_multiple=99.0,
    )
    trades = [
        _trade("2024-01-10", 30.0),
        _trade("2024-02-10", 20.0),
        _trade("2024-03-10", -10.0),
        _trade("2024-04-10", 10.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    monthly = out["monthly"]
    assert monthly["rollback_adjust_count"] == 1
    assert abs(monthly["final_net_value"] - 160.16) < 1e-6


def test_dynamic_compounding_cagr_uses_shared_trade_date_range():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=9_999.0,
        add_ratio=0.5,
        rollback_amount=9_999.0,
        max_multiple=99.0,
    )
    trades = [
        _trade("2024-01-02", 10.0),
        _trade("2024-01-20", 10.0),
        _trade("2024-02-10", 10.0),
    ]
    out = build_dynamic_compounding(trades, cfg)
    weekly = out["weekly"]
    monthly = out["monthly"]

    years = ((datetime(2024, 2, 10) - datetime(2024, 1, 2)).days + 1) / 365.25
    weekly_expected = (weekly["profit_multiple"] ** (1.0 / years) - 1.0) * 100.0
    monthly_expected = (monthly["profit_multiple"] ** (1.0 / years) - 1.0) * 100.0

    assert abs(weekly["cagr_pct"] - weekly_expected) < 1e-6
    assert abs(monthly["cagr_pct"] - monthly_expected) < 1e-6


def test_dynamic_compounding_report_keeps_each_trade_and_adjusts_quantity(tmp_path):
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=10.0,
        add_ratio=1.0,
        rollback_amount=9999.0,
        max_multiple=2.0,
    )
    trades = [
        {
            "trade_date1": "2024-01-01 09:00:00",
            "trade_date2": "2024-01-10 09:00:00",
            "net_profit": 30.0,
            "bs": "B",
            "price1": 100.0,
            "price2": 115.0,
            "report_contract": 2.0,
        },
        {
            "trade_date1": "2024-02-01 09:00:00",
            "trade_date2": "2024-02-10 09:00:00",
            "net_profit": -20.0,
            "bs": "S",
            "price1": 100.0,
            "price2": 105.0,
            "report_contract": 2.0,
        },
    ]

    result = build_dynamic_compounding_report(trades, cfg, "monthly")
    assert len(result["trades"]) == 2
    assert result["trades"][0]["adjusted_contract"] == 2.0
    assert result["trades"][1]["adjusted_contract"] == 4.0
    assert result["trades"][1]["adjusted_net_profit"] == -40.0

    payload = serialize_dynamic_compounding_sea(
        display_name="Demo_每月調整",
        mode="monthly",
        initial_capital=80_000_000,
        trades=result["trades"],
    )
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        event_name = next(name for name in archive.namelist() if name.endswith("/events.jsonl"))
        events = [json.loads(line) for line in archive.read(event_name).decode().splitlines()]
    fund_events = [event for event in events if event["type"] == "fund"]
    trade_events = [event for event in events if event["type"] == "trade"]
    assert fund_events == [
        {
            "timestamp": "2024-01-10T00:00:00Z",
            "type": "fund",
            "data": {"currency": "USD", "amount": 80_000_000.0},
        }
    ]
    assert len(trade_events) == 4
    assert abs(trade_events[0]["data"]["quantity"]) == 2.0
    assert abs(trade_events[2]["data"]["quantity"]) == 4.0
    assert {event["data"]["instrument_id"] for event in trade_events} == {"VPDC"}

    report_path = tmp_path / "dynamic-monthly.sea"
    report_path.write_bytes(payload)
    parsed = parse_file(report_path, strategy_index=0)
    assert abs(sum(item.net_profit for item in parsed) - sum(t["adjusted_net_profit"] for t in result["trades"])) < 1e-6


def test_weekly_and_monthly_download_rows_are_simulated_separately():
    cfg = DynamicCompoundingConfig(
        initial_capital=100.0,
        initial_ratio=0.5,
        add_threshold_profit=10.0,
        add_ratio=1.0,
        rollback_amount=9999.0,
        max_multiple=2.0,
    )
    trades = [
        {"trade_date2": "2024-01-02", "net_profit": 30.0, "report_contract": 2.0},
        {"trade_date2": "2024-01-10", "net_profit": 10.0, "report_contract": 2.0},
    ]

    weekly = build_dynamic_compounding_report(trades, cfg, "weekly")
    monthly = build_dynamic_compounding_report(trades, cfg, "monthly")

    assert [row["adjusted_contract"] for row in weekly["trades"]] == [2.0, 4.0]
    assert [row["adjusted_contract"] for row in monthly["trades"]] == [2.0, 2.0]


def test_sea_export_merges_adjusted_trades_by_close_date_and_uses_one_symbol():
    trades = [
        {"trade_date2": "2024-01-02 09:00:00", "adjusted_contract": 2.0, "adjusted_net_profit": 30.0},
        {"trade_date2": "2024-01-02 13:30:00", "adjusted_contract": 3.0, "adjusted_net_profit": -10.0},
        {"trade_date2": "2024-01-03 10:00:00", "adjusted_contract": 4.0, "adjusted_net_profit": 8.0},
    ]

    payload = serialize_dynamic_compounding_sea(
        display_name="daily",
        mode="weekly",
        initial_capital=80_000_000,
        trades=trades,
    )
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        event_name = next(name for name in archive.namelist() if name.endswith("/events.jsonl"))
        events = [json.loads(line) for line in archive.read(event_name).decode().splitlines()]

    assert len(events) == 5
    assert events[0]["type"] == "fund"
    trade_events = [event for event in events if event["type"] == "trade"]
    assert {event["data"]["instrument_id"] for event in trade_events} == {"VPDC"}
    assert trade_events[0]["data"]["quantity"] == 5.0
    assert trade_events[1]["data"]["quantity"] == -5.0
