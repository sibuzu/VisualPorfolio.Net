from __future__ import annotations

from datetime import datetime
from dataclasses import replace
from decimal import Decimal

import pytest

from strategy_report.analysis import CalculationSettings, _dynamic_compounding_records, _periods, analyze_report
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


def test_half_year_and_quarter_periods_keep_calendar_boundaries():
    records = [
        {"timestamp": datetime(2024, month, 2), "profit": Decimal(profit)}
        for month, profit in [(1, 10), (3, -5), (7, 20), (10, -10)]
    ]
    periods = _periods(records, Decimal(100), True)
    assert [(row["period"], row["profit"]) for row in periods["semiannual"]] == [
        ("2024/H1", 5), ("2024/H2", 10)]
    assert [(row["period"], row["profit"]) for row in periods["quarterly"]] == [
        ("2024/Q1", 5), ("2024/Q3", 20), ("2024/Q4", -10)]
    assert periods["semiannual"][0]["mdd"] == 5
    assert periods["semiannual"][1]["mdd"] == 10


def test_simple_curve_position_matches_csharp_three_event_peak():
    events = tuple(
        TradeEvent(index, datetime(2024, 1, 2, 9 + index), side, Decimal(1), Decimal(100), "TXF")
        for index, side in enumerate(("B", "S", "B", "S", "B", "S"))
    )
    report = analyze_report(replace(_source(), events=events), CalculationSettings(mode="backtest"))
    assert [row["open_position"] for row in report["simple"]["curve"]] == [1] * len(events)


def test_simple_curve_position_returns_to_zero_after_three_flat_events():
    events = (
        TradeEvent(0, datetime(2024, 1, 2, 9), "B", Decimal(1), Decimal(100), "TXF"),
        TradeEvent(1, datetime(2024, 1, 2, 10), "S", Decimal(1), Decimal(100), "TXF"),
        *(TradeEvent(index, datetime(2024, 1, 2, 9 + index), "N", Decimal(0), Decimal(100), "TXF")
          for index in range(2, 5)),
    )
    report = analyze_report(replace(_source(), events=events), CalculationSettings(mode="backtest"))
    assert [row["open_position"] for row in report["simple"]["curve"]] == [1, 1, 1, 0, 0]


def test_backtest_capital_fallback_and_no_rescaling():
    report = analyze_report(_source(initial=None), CalculationSettings(mode="backtest", fixed_quantity=Decimal(9)))
    assert report["compound"]["summary"]["initial_capital"] == 100_000
    assert report["compound"]["summary"]["final_capital"] == 102_000
    assert report["compound"]["detail"][0]["quantity"] == 2


@pytest.mark.parametrize("source_capital,manual_capital", [
    (None, Decimal(150_000)), (Decimal(50_000), Decimal(100_000)),
])
def test_backtest_manual_capital_changes_returns_without_changing_trades(source_capital, manual_capital):
    source = _source(initial=source_capital)
    automatic = analyze_report(source, CalculationSettings(mode="backtest"))
    manual = analyze_report(source, CalculationSettings(
        mode="backtest", backtest_initial_capital=manual_capital))
    original = automatic["compound"]["summary"]
    changed = manual["compound"]["summary"]
    assert original["initial_capital"] == (source_capital or 100_000)
    assert changed["initial_capital"] == manual_capital
    assert changed["net_profit"] == original["net_profit"] == 2_000
    assert changed["final_capital"] == manual_capital + 2_000
    assert [row["quantity"] for row in manual["compound"]["detail"]] == [2, 2]
    assert changed["annual_return_pct"] < original["annual_return_pct"]


@pytest.mark.parametrize("threshold,expected_multipliers", [
    ("1.01%", [10, 10, 15, 10, 15]),
    ("2000", [10, 10, 15, 15, 15]),
])
def test_dynamic_compounding_switches_at_week_boundaries(threshold, expected_multipliers):
    simple_records = [
        {"timestamp": datetime(2024, 1, day, 9), "profit": Decimal(profit),
         "ref_price": Decimal(100), "skip": False}
        for day, profit in [(2, -1000), (3, 1200), (9, -100), (16, 200), (23, 100)]
    ]
    cfg = CalculationSettings(
        mode="dynamic_compounding", initial_capital=100_000,
        dynamic_profit_threshold=1000, dynamic_drawdown_threshold=threshold,
        dynamic_lot_rounding="floor")
    records, detail = _dynamic_compounding_records(simple_records, _source(), cfg)
    assert [int(row["multiplier"]) for row in records] == expected_multipliers
    assert [row["profit"] for row in records[:3]] == [-10_000, 12_000, -1_500]
    assert records[-1]["equity"] == sum((row["profit"] for row in records), Decimal(100_000))
    assert detail[-1]["action"] == "動態複利(ByWeek)"


def test_dynamic_compounding_monthly_interval_and_risk_cap():
    simple_records = [
        {"timestamp": datetime(2024, month, day, 9), "profit": Decimal(profit),
         "ref_price": Decimal(100), "skip": False}
        for month, day, profit in [(1, 2, -1000), (1, 3, 1200), (1, 9, 100), (2, 2, 100)]
    ]
    cfg = CalculationSettings(
        mode="dynamic_compounding", initial_capital=100_000,
        dynamic_profit_threshold=1000, dynamic_interval="monthly",
        dynamic_max_multiple=1, dynamic_lot_rounding="floor")
    records, detail = _dynamic_compounding_records(simple_records, _source(), cfg)
    assert [row["multiplier"] for row in records] == [10, 10, 10, 10]
    assert detail[-1]["action"] == "動態複利(ByMonth)"


def test_dynamic_compounding_is_available_in_complete_report():
    report = analyze_report(_source(initial=None), CalculationSettings(
        mode="dynamic_compounding", initial_capital=100_000))
    compound = report["compound"]
    assert compound["summary"]["initial_capital"] == 100_000
    assert compound["summary"]["final_capital"] == 102_000
    assert compound["detail"][0]["action"] == "動態複利(ByWeek)"
    assert compound["detail"][0]["multiplier"] == 1


@pytest.mark.parametrize("rounding,expected", [
    ("floor", Decimal(2)), ("ceil", Decimal(3)),
    ("round", Decimal(3)), ("retain", Decimal("2.5")),
])
def test_dynamic_compounding_lot_rounding_matches_csharp(rounding, expected):
    records, _ = _dynamic_compounding_records([{
        "timestamp": datetime(2024, 1, 2, 9), "profit": Decimal(-1000),
        "ref_price": Decimal(100), "skip": False,
    }], _source(), CalculationSettings(
        mode="dynamic_compounding", initial_capital=100_000,
        dynamic_initial_ratio=Decimal("0.025"), dynamic_lot_rounding=rounding))
    assert records[0]["multiplier"] == expected


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
    assert filtered["compound"]["summary"]["initial_capital"] == 100000
    assert filtered["compound"]["detail"] == []


@pytest.mark.parametrize("entry,exit", [("B", "S"), ("S", "B")])
def test_range_excludes_carried_trade_until_flat(entry, exit):
    events = tuple(TradeEvent(i, datetime(2025, 1, i + 1, 9), side, Decimal(qty), Decimal(price), "TXF")
                   for i, (side, qty, price) in enumerate([
                       (entry, 2, 100), (exit, 1, 101), (exit, 1, 102),
                       (entry, 2, 103), (exit, 2, 105)]))
    source = replace(_source(slippage="0.5"), events=events)
    report = analyze_report(source, CalculationSettings(date_start="2025-01-02"))
    for name in ("simple", "compound"):
        section = report[name]
        assert [row["side"] for row in section["detail"]] == [entry, exit]
        assert section["detail"][0]["timestamp"] == "2025-01-04 09:00:00"
        assert section["detail"][0]["profit"] == -200
        assert section["summary"]["net_profit"] == (400 if entry == "B" else -1200)
        assert section["periods"]["annual"][0]["profit"] == section["summary"]["net_profit"]
    disabled = analyze_report(source, CalculationSettings(date_start="2025-01-02", date_range_enabled=False))
    assert len(disabled["simple"]["detail"]) == 5


@pytest.mark.parametrize("entry,exit", [("B", "S"), ("S", "B")])
def test_range_mark_creates_cost_free_opening_position(entry, exit):
    source = replace(_source(slippage="0.5"), events=(
        TradeEvent(0, datetime(2025, 1, 1, 9), entry, Decimal(2), Decimal(100), "TXF"),
        TradeEvent(1, datetime(2025, 1, 2, 9), "N", Decimal(0), Decimal(105), "TXF"),
        TradeEvent(2, datetime(2025, 1, 3, 9), exit, Decimal(2), Decimal(110), "TXF"),
    ))
    report = analyze_report(source, CalculationSettings(date_start="2025-01-02"))
    for name in ("simple", "compound"):
        section = report[name]
        assert len(section["detail"]) == 1
        assert section["detail"][0]["position"] == 0
        assert section["summary"]["net_profit"] == (1800 if entry == "B" else -2200)
        assert section["summary"]["trade_count"] == 1


def test_range_reversal_keeps_only_new_position():
    source = replace(_source(slippage="0.5"), events=(
        TradeEvent(0, datetime(2025, 1, 1, 9), "B", Decimal(2), Decimal(100), "TXF"),
        TradeEvent(1, datetime(2025, 1, 2, 9), "S", Decimal(3), Decimal(105), "TXF"),
        TradeEvent(2, datetime(2025, 1, 3, 9), "B", Decimal(1), Decimal(100), "TXF"),
    ))
    report = analyze_report(source, CalculationSettings(date_start="2025-01-02"))
    for name in ("simple", "compound"):
        assert [row["quantity"] for row in report[name]["detail"]] == [1, 1]
        assert [row["position"] for row in report[name]["detail"]] == [-1, 0]
        assert report[name]["summary"]["net_profit"] == 800


def test_range_end_keeps_open_position_without_exit_cost():
    source = replace(_source(slippage="0.5"), events=(
        TradeEvent(0, datetime(2025, 1, 1, 9), "B", Decimal(2), Decimal(100), "TXF"),
        TradeEvent(1, datetime(2025, 1, 2, 23, 59), "N", Decimal(0), Decimal(105), "TXF"),
        TradeEvent(2, datetime(2025, 1, 3, 9), "S", Decimal(2), Decimal(110), "TXF"),
    ))
    report = analyze_report(source, CalculationSettings(date_end="2025-01-02"))
    for name in ("simple", "compound"):
        assert len(report[name]["detail"]) == 1
        assert report[name]["detail"][0]["position"] == 2
        assert report[name]["summary"]["net_profit"] == 1800
        assert report[name]["curve"][-1]["timestamp"] == "2025-01-02 23:59:00"


def test_managed_range_restarts_capital_and_sizing():
    source = replace(_source(), events=_source().events + (
        TradeEvent(2, datetime(2024, 2, 1, 9), "B", Decimal(1), Decimal(100), "TXF"),
        TradeEvent(3, datetime(2024, 2, 2, 9), "S", Decimal(1), Decimal(110), "TXF"),
    ))
    report = analyze_report(source, CalculationSettings(mode="fixed_amount", initial_capital=100000,
                           amount_per_quantity=100000, date_start="2024-02-01"))
    assert report["compound"]["summary"]["initial_capital"] == 100000
    assert report["compound"]["detail"][0]["quantity"] == 1
    assert report["simple"]["detail"][0]["equity"] == 0


def test_range_tracks_overlapping_strategies_independently():
    source = replace(_source(), events=(
        TradeEvent(0, datetime(2025, 1, 1, 9), "B", Decimal(2), Decimal(100), "TXF", strategy_index=1),
        TradeEvent(1, datetime(2025, 1, 2, 9), "B", Decimal(1), Decimal(100), "TXF", strategy_index=2),
        TradeEvent(2, datetime(2025, 1, 3, 9), "S", Decimal(2), Decimal(105), "TXF", strategy_index=1),
        TradeEvent(3, datetime(2025, 1, 4, 9), "S", Decimal(1), Decimal(110), "TXF", strategy_index=2),
    ))
    report = analyze_report(source, CalculationSettings(date_start="2025-01-02"))
    for name in ("simple", "compound"):
        assert [row["strategy"] for row in report[name]["detail"]] == [2, 2]
        assert report[name]["summary"]["net_profit"] == 2000


def test_cwbkrr_range_starts_at_next_buy():
    old_quantity = Decimal("261.2671456564337034617896800")
    new_quantity = Decimal("264.0264026402640264026402640")
    source = replace(_source(slippage="0.01%"), point_value=Decimal(40), events=(
        TradeEvent(0, datetime(2024, 12, 31, 13, 30), "B", old_quantity, Decimal("1913.75"), "TWN"),
        TradeEvent(1, datetime(2025, 1, 2, 9), "S", old_quantity, Decimal(1906), "TWN"),
        TradeEvent(2, datetime(2025, 1, 2, 13, 30), "B", new_quantity, Decimal("1893.75"), "TWN"),
        TradeEvent(3, datetime(2025, 1, 3, 9), "S", new_quantity, Decimal(1906), "TWN"),
    ))
    report = analyze_report(source, CalculationSettings(date_start="2025-01-01", date_end="2026-10-24"))
    for name in ("simple", "compound"):
        assert report[name]["detail"][0]["timestamp"] == "2025-01-02 13:30:00"
        assert [row["side"] for row in report[name]["detail"]] == ["B", "S"]
        assert [round(row["profit"]) for row in report[name]["detail"]] == [-2000, 127360]


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
    annual = report["compound"]["periods"]["annual"][0]
    assert annual["return_pct"] == pytest.approx(1000 / 100_000 * 100)
    assert annual["mdd_pct"] == pytest.approx(1000 / 102_000 * 100)
    assert report["compound"]["periods"]["monthly"][1]["mdd_pct"] == pytest.approx(
        1000 / 102_000 * 100)


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
    {"mode": "backtest", "backtest_initial_capital": 0},
    {"mode": "dynamic_compounding", "dynamic_drawdown_threshold": "five percent"},
    {"mode": "fixed_quantity", "date_start": "2024-02-01", "date_end": "2024-01-01"},
])
def test_invalid_settings_are_rejected(settings: dict):
    with pytest.raises(ValueError):
        CalculationSettings(**settings)
