from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import get_args

import pytest
from pydantic import ValidationError

from strategy_report import buy_hold as bh
from strategy_report.analysis import CalculationSettings, Mode
from strategy_report.main import analyze_with_reference
from strategy_report.model import ReportSource, TradeEvent


def source():
    return ReportSource("srp", "demo.srp", "Demo", "TX", {}, {}, (
        TradeEvent(0, datetime(2024, 1, 2, 9), "B", Decimal(1), Decimal(100), "TX"),
        TradeEvent(1, datetime(2024, 1, 5, 9), "S", Decimal(1), Decimal(110), "TX"),
    ), period_start="2024/1/1", period_end="2024/01/05")


@pytest.fixture(autouse=True)
def clear_market_cache():
    cached = bh._market_data
    cached.cache_clear()
    yield
    cached.cache_clear()


def test_date_precedence_and_trade_fallback():
    report = source()
    assert bh.reference_range(report, None, None) == (date(2024, 1, 1), date(2024, 1, 5))
    assert bh.reference_range(report, date(2024, 1, 3), date(2024, 1, 4)) == (date(2024, 1, 3), date(2024, 1, 4))
    assert bh.reference_range(replace(report, period_start="bad", period_end=""), None, None) == (date(2024, 1, 2), date(2024, 1, 5))
    marker = TradeEvent(0, datetime(2023, 12, 1), "P", Decimal(0), Decimal(99), "TX")
    assert bh.reference_range(replace(report, period_start="", events=(marker,) + report.events), None, None)[0] == date(2024, 1, 2)


def test_none_never_fetches_market_data(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: pytest.fail("No benchmark should request market data"))
    assert analyze_with_reference(source(), CalculationSettings())["buy_hold"] is None


def test_unchecked_dates_do_not_limit_reference(monkeypatch):
    calls = []
    def market(product, code, start, end, hour):
        calls.append((start, end))
        return [{"date": "2024-01-02", "close": 100}, {"date": "2024-01-05", "close": 110}], []
    monkeypatch.setattr(bh, "_market_data", market)
    result = analyze_with_reference(source(), CalculationSettings(
        buy_hold={}, date_start="2024-01-04", date_end="2024-01-04", date_range_enabled=False))
    assert calls == [(date(2024, 1, 1), date(2024, 1, 5))]
    assert result["buy_hold"]["start_date"] == "2024-01-02"


def test_stock_reinvests_dividends_and_accounts_for_splits():
    rows = [{"date": "2024-01-02", "close": 100}, {"date": "2024-01-03", "close": 98},
            {"date": "2024-01-04", "close": 25}, {"date": "2024-01-08", "close": 50}]
    dividends = [{"date": "2024-01-10", "CashExDividendTradingDate": "2024-01-03", "CashEarningsDistribution": 2}]
    curve = bh._stock_curve(rows, dividends * 2, date(2024, 1, 1), date(2024, 1, 5), Decimal(10000))
    assert [row["equity"] for row in curve] == pytest.approx([10000, 10000, 10000 / 98 * 100])
    assert curve[0]["timestamp"] == "2024-01-02"  # Holiday start advances to first quote.
    assert curve[-1]["timestamp"] == "2024-01-04"  # Never includes prices beyond the report.
    # Buying on the ex-date does not receive that dividend.
    ex_day_curve = bh._stock_curve(rows, dividends, date(2024, 1, 3), date(2024, 1, 3), Decimal(10000))
    assert ex_day_curve[0]["equity"] == 10000


def test_futures_rollover_excludes_contract_spread_and_night_session():
    rows = [
        {"date": "2024-01-02", "contract_date": "202401", "close": 100},
        {"date": "2024-01-02", "contract_date": "202402", "close": 110},
        {"date": "2024-01-03", "contract_date": "202401", "close": 102},
        {"date": "2024-01-03", "contract_date": "202402", "close": 112},
        {"date": "2024-01-04", "contract_date": "202402", "close": 113},
        {"date": "2024-01-04", "contract_date": "202402", "close": 1000, "trading_session": "after_market"},
        {"date": "2024-01-04", "contract_date": "202401/202402", "close": 1},
    ]
    curve = bh._futures_curve(rows, date(2024, 1, 1), date(2024, 1, 5), Decimal(10000), Decimal(5))
    assert [row["equity"] for row in curve] == [10000, 11000, 11500]


def test_benchmark_is_identical_across_all_strategy_modes_and_capitals(monkeypatch):
    calls = []
    def fetch(dataset, code, start, end):
        calls.append((dataset, code, start, end))
        return [] if dataset == "TaiwanStockDividend" else [
            {"date": "2024-01-02", "close": 100}, {"date": "2024-01-05", "close": 110}]
    monkeypatch.setattr(bh, "_fetch_rows", fetch)
    expected = None
    for index, mode in enumerate(get_args(Mode)):
        settings = CalculationSettings(mode=mode, initial_capital=100000 * (index + 1), chip_size=10000,
                                       fixed_quantity=index + 1, buy_hold={"amount_wan": 100})
        result = analyze_with_reference(source(), settings)["buy_hold"]
        if expected is None:
            expected = result
        assert result == expected
        assert result["final_capital"] == 1100000
    assert len(calls) == 2  # One price + one dividend request for every capital mode combined.
    assert expected["name"] == "BH0050_100萬"
    assert expected["requested_start"] == "2024-01-01"
    assert expected["start_date"] == "2024-01-02"


@pytest.mark.parametrize("failure", ["network", "empty"])
def test_market_failure_preserves_strategy_report(monkeypatch, failure):
    def fetch(*args):
        if failure == "network":
            raise bh.BuyHoldError("行情暫時無法提供")
        return []
    monkeypatch.setattr(bh, "_fetch_rows", fetch)
    result = analyze_with_reference(source(), CalculationSettings(buy_hold={}))
    assert result["simple"]["summary"]["net_profit"] == 10
    assert result["buy_hold"]["error"]
    assert result["buy_hold"]["curve"] == []


@pytest.mark.parametrize("settings", [{"amount_wan": 0}, {"amount_wan": "NaN"}, {"leverage": 0},
                                      {"leverage": "Infinity"}, {"code": ""}, {"code": "../TX"}, {"date": "2024-01-01"}])
def test_invalid_benchmark_settings_are_rejected(settings):
    with pytest.raises(ValidationError):
        CalculationSettings(buy_hold=settings)


def test_benchmark_name_normalization():
    assert bh.BuyHoldSettings(product_type="期貨", code=" tx ", amount_wan="100.0", leverage="2.50").name == "BHTX_100萬_2.5X"
