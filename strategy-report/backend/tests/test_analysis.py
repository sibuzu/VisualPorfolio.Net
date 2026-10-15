from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from strategy_report.analysis import CalculationSettings, analyze_report
from strategy_report.model import ReportSource, TradeEvent


def _source(*, initial: Decimal | None = Decimal(80_000_000), slippage: str = "0") -> ReportSource:
    events = (
        TradeEvent(0, datetime(2024, 1, 2, 9), "B", Decimal(2), Decimal(100), "TXF", atr=Decimal(10)),
        TradeEvent(1, datetime(2024, 1, 3, 9), "S", Decimal(2), Decimal(105), "TXF", atr=Decimal(10)),
    )
    return ReportSource("srp", "demo.srp", "Demo", "TXF", {}, {}, events,
                        point_value=Decimal(200), slippage=slippage, initial_capital=initial)


def test_simple_and_backtest_capital():
    report = analyze_report(_source(), CalculationSettings(mode="backtest"))
    assert report["simple"]["summary"]["net_profit"] == 2000
    assert report["compound"]["summary"]["initial_capital"] == 80_000_000
    assert report["compound"]["summary"]["final_capital"] == 80_002_000
    assert [row["quantity"] for row in report["compound"]["detail"]] == [2, 2]
    assert report["compound"]["periods"]["daily"][-1]["cumulative"] == 80_002_000


def test_backtest_capital_fallback_and_no_rescaling():
    report = analyze_report(_source(initial=None), CalculationSettings(mode="backtest", fixed_quantity=Decimal(9)))
    assert report["compound"]["summary"]["initial_capital"] == 100_000
    assert report["compound"]["summary"]["final_capital"] == 102_000
    assert report["compound"]["detail"][0]["quantity"] == 2


@pytest.mark.parametrize("settings,expected_quantity,expected_profit", [
    ({"mode": "fixed_quantity", "fixed_quantity": 3}, 6, 6000),
    ({"mode": "fixed_amount", "amount_per_quantity": 500_000}, 4, 4000),
    ({"mode": "risk_factor", "risk_factor": 0.002}, 2, 2000),
    ({"mode": "target_leverage", "leverage": 0.2}, 10, 10000),
    ({"mode": "profit_step", "initial_quantity": 4, "maximum_quantity": 2}, 4, 4000),
    ({"mode": "fixed_risk", "fixed_risk_ratio": 0.02, "loss_per_trade": 10_000}, 4, 4000),
    ({"mode": "profit_risk", "initial_risk_ratio": 0.02, "loss_per_trade": 10_000}, 4, 4000),
    ({"mode": "target_margin", "margin_ratio": 0.1, "margin_per_quantity": 100_000}, 2, 2000),
    ({"mode": "kelly", "stake_percent": 10, "chip_size": 100_000}, 2, 2000),
])
def test_capital_modes(settings: dict, expected_quantity: float, expected_profit: float):
    report = analyze_report(_source(), CalculationSettings(**settings))
    compound = report["compound"]
    assert compound["detail"][0]["quantity"] == expected_quantity
    assert compound["summary"]["net_profit"] == expected_profit


def test_range_replays_earlier_profit():
    original = _source()
    events = original.events + (
        TradeEvent(2, datetime(2024, 2, 1, 9), "B", Decimal(1), Decimal(100), "TXF"),
        TradeEvent(3, datetime(2024, 2, 2, 9), "S", Decimal(1), Decimal(110), "TXF"),
    )
    source = ReportSource("srp", "demo.srp", "Demo", "TXF", {}, {}, events,
                          point_value=Decimal(200), initial_capital=Decimal(100_000))
    report = analyze_report(source, CalculationSettings(mode="backtest", date_start="2024-02-01"))
    compound = report["compound"]
    assert compound["summary"]["initial_capital"] == 102_000
    assert compound["summary"]["net_profit"] == 2_000
    assert compound["summary"]["final_capital"] == 104_000
    assert len(compound["detail"]) == 2


def test_slippage_is_charged_to_trade_profit():
    report = analyze_report(_source(slippage="0.5"), CalculationSettings(mode="backtest"))
    assert report["simple"]["summary"]["net_profit"] == 1600


@pytest.mark.parametrize("direction", ["long", "short"])
@pytest.mark.parametrize("slippage", ["0.5", "0.1%"])
def test_compound_execution_costs_match_simple_entry_and_exit(direction, slippage):
    entry_side, exit_side = ("B", "S") if direction == "long" else ("S", "B")
    entry_price, exit_price = Decimal(100), Decimal(105)
    events = (
        TradeEvent(0, datetime(2024, 1, 2, 9), entry_side, Decimal(2), entry_price, "TXF"),
        TradeEvent(1, datetime(2024, 1, 3, 9), exit_side, Decimal(2), exit_price, "TXF"),
    )
    source = ReportSource("srp", "costs.srp", "Costs", "TXF", {}, {}, events,
                          point_value=Decimal(200), slippage=slippage)
    entry_cost = 200 if slippage == "0.5" else 40
    exit_cost = 200 if slippage == "0.5" else 42
    gross = 2000 if direction == "long" else -2000
    for mode, multiplier in (("backtest", 1), ("fixed_quantity", 3)):
        result = analyze_report(source, CalculationSettings(mode=mode, fixed_quantity=3))
        compound = result["compound"]
        expected = [-entry_cost * multiplier, (gross - exit_cost) * multiplier]
        assert [row["profit"] for row in compound["detail"]] == expected
        assert [row["profit"] for row in compound["curve"]] == expected
        assert compound["summary"]["net_profit"] == sum(expected)
        assert compound["periods"]["annual"][0]["profit"] == sum(expected)
        assert [row["profit"] * multiplier for row in result["simple"]["detail"]] == expected


def test_mark_updates_do_not_charge_future_exit_cost():
    events = (
        TradeEvent(0, datetime(2024, 1, 2, 9), "B", Decimal(2), Decimal(100), "TXF"),
        TradeEvent(1, datetime(2024, 1, 3, 9), "P", Decimal(0), Decimal(105), "TXF"),
        TradeEvent(2, datetime(2024, 1, 4, 9), "S", Decimal(2), Decimal(105), "TXF"),
    )
    source = ReportSource("sea", "costs.sea", "Costs", "TXF", {}, {}, events,
                          point_value=Decimal(200), slippage="0.5")
    report = analyze_report(source, CalculationSettings(initial_capital=100000))
    assert [row["profit"] for row in report["compound"]["curve"]] == [-200, 2000, -200]
    assert [row["equity"] for row in report["compound"]["curve"]] == [99800, 101800, 101600]
    filtered = analyze_report(source, CalculationSettings(initial_capital=100000, date_start="2024-01-04"))
    assert filtered["compound"]["summary"]["initial_capital"] == 101800
    assert filtered["compound"]["detail"][0]["profit"] == -200


def test_cwbkrr_first_pair_charges_each_execution_separately():
    quantity = Decimal("450.755014649538")
    source = ReportSource("srp", "cost-regression.srp", "Costs", "TWN", {}, {}, (
        TradeEvent(0, datetime(2020, 10, 16, 13, 30), "B", quantity, Decimal("1109.25"), "TWN"),
        TradeEvent(1, datetime(2020, 10, 29, 12, 58), "S", quantity, Decimal("1104.25"), "TWN"),
    ), point_value=Decimal(40), slippage="0.01%")
    report = analyze_report(source, CalculationSettings(fixed_quantity=1))
    rows = report["compound"]["detail"]
    assert [round(row["profit"]) for row in rows] == [-2000, -92142]
    assert rows[0]["equity"] == pytest.approx(998000)
    assert rows[1]["equity"] == pytest.approx(905858.0121703854)
    assert [row["profit"] for row in rows] == [row["profit"] for row in report["simple"]["detail"]]


def test_summary_win_loss_totals_and_period_drawdowns():
    original = _source()
    events = original.events + (
        TradeEvent(2, datetime(2024, 2, 1, 9), "B", Decimal(1), Decimal(100), "TXF"),
        TradeEvent(3, datetime(2024, 2, 2, 9), "S", Decimal(1), Decimal(95), "TXF"),
    )
    source = ReportSource("srp", "demo.srp", "Demo", "TXF", {}, {}, events, point_value=Decimal(200))
    report = analyze_report(source, CalculationSettings(mode="backtest"))
    for name in ("simple", "compound"):
        section = report[name]
        summary = section["summary"]
        assert summary["winning_profit"] == 2000
        assert summary["losing_profit"] == -1000
        assert summary["winning_profit"] + summary["losing_profit"] == summary["net_profit"]
        assert summary["winning_count"] + summary["losing_count"] == summary["trade_count"]
        assert [row["mdd"] for row in section["periods"]["monthly"]] == [0, 1000]
        assert section["periods"]["annual"][0]["mdd"] == 1000


def test_losing_trade_and_overlapping_strategies():
    original = _source()
    loss_events = (
        original.events[0],
        TradeEvent(1, datetime(2024, 1, 3, 9), "S", Decimal(2), Decimal(95), "TXF"),
    )
    loss_source = ReportSource("srp", "loss.srp", "Demo", "TXF", {}, {}, loss_events,
                               point_value=Decimal(200), initial_capital=Decimal(80_000_000))
    loss = analyze_report(loss_source, CalculationSettings(mode="backtest"))
    assert loss["simple"]["summary"]["net_profit"] == -2000
    assert loss["compound"]["summary"]["final_capital"] == 79_998_000

    overlap_events = (
        TradeEvent(0, datetime(2024, 1, 2, 9), "B", Decimal(1), Decimal(100), "TXF", strategy_index=1),
        TradeEvent(1, datetime(2024, 1, 2, 9, 5), "B", Decimal(1), Decimal(100), "TXF", strategy_index=2),
        TradeEvent(2, datetime(2024, 1, 3, 9), "S", Decimal(1), Decimal(105), "TXF", strategy_index=1),
        TradeEvent(3, datetime(2024, 1, 3, 9, 5), "S", Decimal(1), Decimal(105), "TXF", strategy_index=2),
    )
    overlap_source = ReportSource("srp", "overlap.srp", "Demo", "TXF", {}, {}, overlap_events,
                                  point_value=Decimal(200), initial_capital=Decimal(80_000_000))
    overlap = analyze_report(overlap_source, CalculationSettings(mode="backtest"))
    assert overlap["simple"]["summary"]["net_profit"] == 2000
    assert overlap["compound"]["summary"]["final_capital"] == 80_002_000
    assert overlap["simple"]["summary"]["trade_count"] == 2
    assert overlap["compound"]["summary"]["trade_count"] == 4
    assert len(overlap["simple"]["detail"]) == 4


@pytest.mark.parametrize("settings", [
    {"mode": "kelly", "chip_size": 0},
    {"mode": "fixed_risk", "loss_per_trade": 0},
    {"mode": "target_margin", "margin_per_quantity": 0},
    {"mode": "fixed_quantity", "initial_capital": "NaN"},
    {"mode": "fixed_quantity", "date_start": "2024-02-01", "date_end": "2024-01-01"},
])
def test_invalid_settings_are_rejected(settings: dict):
    with pytest.raises(ValueError):
        CalculationSettings(**settings)
