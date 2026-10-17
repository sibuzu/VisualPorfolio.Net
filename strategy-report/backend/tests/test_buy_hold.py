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
    _, detail = bh._stock_history(rows, dividends, date(2024, 1, 1), date(2024, 1, 5),
                                  Decimal(10000), "0050")
    assert detail[-1]["action"] == "分割／賣出"
    # Buying on the ex-date does not receive that dividend.
    ex_day_curve = bh._stock_curve(rows, dividends, date(2024, 1, 3), date(2024, 1, 3), Decimal(10000))
    assert ex_day_curve[0]["equity"] == 10000


def test_stock_daily_close_values_end_with_a_sale(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "open": 105, "close": 100},
        {"date": "2024-01-03", "open": 200, "close": 110},
        {"date": "2024-01-05", "open": 300, "close": 120},
    ], []))
    result = bh.analyze_buy_hold(source(), bh.BuyHoldSettings(amount_wan=1))
    assert [row["equity"] for row in result["curve"]] == [10000, 11000, 12000]
    assert [row["side"] for row in result["detail"]] == ["B", "M", "S"]
    assert [row["price"] for row in result["detail"]] == [100, 110, 120]
    assert [row["profit"] for row in result["detail"]] == [0, 1000, 1000]
    assert result["detail"][-1]["position"] == 0
    assert result["final_capital"] == 12000


def test_buy_hold_performance_uses_daily_equity_for_periods_and_drawdowns(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2023-12-29", "close": 100},
        {"date": "2024-01-02", "close": 120},
        {"date": "2024-01-03", "close": 90},
        {"date": "2024-01-04", "close": 130},
        {"date": "2024-01-05", "close": 110},
    ], []))
    report = replace(source(), period_start="2023/12/29")
    result = bh.analyze_buy_hold(report, bh.BuyHoldSettings(amount_wan=1))
    assert result["summary"]["initial_capital"] == 10000
    assert result["summary"]["final_capital"] == 11000
    assert result["summary"]["annual_return_pct"] > 0
    assert result["summary"]["max_drawdown"] == 3000
    assert result["drawdowns"][0] == {
        "amount": 3000, "percent": 25, "started_at": "2024-01-02",
        "bottomed_at": "2024-01-03", "recovered_at": "2024-01-04",
    }
    assert [(row["period"], row["profit"], row["return_pct"])
            for row in result["periods"]["annual"]] == [("2023", 0, 0), ("2024", 1000, 10)]
    assert result["periods"]["monthly"][1]["mdd_pct"] == 25
    assert result["periods"]["monthly"][1]["mdd"] == 3000
    assert [row["period"] for row in result["periods"]["semiannual"]] == ["2023/H2", "2024/H1"]
    assert result["periods"]["quarterly"][1]["mdd"] == 3000


def test_stock_detail_marks_dividends_and_updates_share_count():
    rows = [{"date": f"2024-01-0{day}", "close": 100} for day in range(2, 7)]
    dividends = [
        {"CashExDividendTradingDate": "2024-01-03", "CashEarningsDistribution": 1},
        {"StockExDividendTradingDate": "2024-01-04", "StockEarningsDistribution": 1},
        {"CashExDividendTradingDate": "2024-01-05", "CashEarningsDistribution": 1,
         "StockExDividendTradingDate": "2024-01-05", "StockEarningsDistribution": 1},
    ]
    _, detail = bh._stock_history(rows, dividends, date(2024, 1, 2), date(2024, 1, 6),
                                  Decimal(10000), "0050")
    assert [row["action"] for row in detail] == ["買進", "除息", "除權", "除權息", "賣出"]
    assert detail[0]["quantity"] == 100
    assert detail[1]["quantity"] == 101
    assert detail[2]["quantity"] == pytest.approx(111.1)
    assert detail[3]["quantity"] > detail[2]["quantity"]
    assert detail[4]["quantity"] == detail[3]["quantity"]


def test_final_stock_dividend_remains_visible_on_sale():
    rows = [{"date": "2024-01-02", "close": 100}, {"date": "2024-01-03", "close": 99}]
    dividends = [{"CashExDividendTradingDate": "2024-01-03", "CashEarningsDistribution": 1}]
    _, detail = bh._stock_history(rows, dividends, date(2024, 1, 2), date(2024, 1, 3),
                                  Decimal(10000), "0050")
    assert detail[-1]["action"] == "除息／賣出"
    assert detail[-1]["quantity"] > detail[0]["quantity"]


def test_single_close_day_has_both_buy_and_sell(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "open": 110, "close": 100}], []))
    result = bh.analyze_buy_hold(source(), bh.BuyHoldSettings(amount_wan=1))
    assert [row["side"] for row in result["detail"]] == ["B", "S"]
    assert result["detail"][-1]["equity"] == 10000


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


def test_futures_detail_marks_both_rollover_legs_without_changing_contracts():
    rows = [
        {"date": "2024-01-02", "contract_date": "202401", "close": 100},
        {"date": "2024-01-02", "contract_date": "202402", "close": 110},
        {"date": "2024-01-03", "contract_date": "202401", "close": 0, "settlement_price": 102},
        {"date": "2024-01-03", "contract_date": "202402", "close": 112},
        {"date": "2024-01-04", "contract_date": "202402", "close": 113},
        {"date": "2024-01-05", "contract_date": "202402", "close": 114},
    ]
    curve, detail = bh._futures_history(rows, date(2024, 1, 2), date(2024, 1, 5),
                                        Decimal(10000), Decimal(5), "TX")
    assert [row["action"] for row in detail] == ["買進", "換倉賣出", "換倉買進", "淨值", "賣出"]
    assert [row["contract"] for row in detail] == ["202401", "202401", "202402", "202402", "202402"]
    assert [row["equity"] for row in curve[:3]] == [10000, 11000, 11500]
    assert detail[1]["quantity"] == 2.5
    assert detail[1]["price"] == 102
    assert detail[1]["price_basis"] == "結算"
    assert detail[1]["position"] == 0
    assert detail[2]["price"] == 112
    assert detail[2]["price_basis"] == "收盤"
    assert detail[2]["profit"] == 0
    assert detail[2]["equity"] == detail[1]["equity"]
    assert detail[2]["quantity"] == detail[1]["quantity"] == 2.5
    assert all(row["quantity"] == 2.5 for row in detail)
    assert detail[3]["profit"] == pytest.approx(detail[2]["quantity"] * 200)


def test_futures_liquidation_keeps_the_funding_history(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "contract_date": "202401", "close": 100},
        {"date": "2024-01-03", "contract_date": "202401", "close": 79},
        {"date": "2024-01-04", "contract_date": "202402", "close": 80},
    ], []))
    result = bh.analyze_buy_hold(source(), bh.BuyHoldSettings(
        product_type="期貨", code="TX", amount_wan=1, leverage=5))
    assert [row["equity"] for row in result["curve"]] == [10000, -500]
    assert [row["action"] for row in result["detail"]] == ["買進", "資金耗盡"]
    assert result["detail"][-1]["position"] == 0
    assert result["initial_capital"] == 10000
    assert result["final_capital"] == -500
    assert result["end_date"] == "2024-01-03"
    assert "2024-01-03" in result["error"]


def test_futures_daily_close_values_end_with_a_sale(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "contract_date": "202401", "open": 105, "close": 100},
        {"date": "2024-01-03", "contract_date": "202401", "open": 150, "close": 102},
        {"date": "2024-01-05", "contract_date": "202401", "open": 200, "close": 103},
    ], []))
    result = bh.analyze_buy_hold(source(), bh.BuyHoldSettings(
        product_type="期貨", code="TX", amount_wan=1, leverage=5))
    assert [row["equity"] for row in result["curve"]] == [10000, 11000, 11500]
    assert [row["side"] for row in result["detail"]] == ["B", "M", "S"]
    assert result["detail"][0]["quantity"] == 2.5  # 50,000 / (100 points × 200 NTD)
    assert result["detail"][-1]["position"] == 0


def test_tx_leverage_uses_contract_point_value_without_changing_exposure():
    rows = [
        {"date": "2024-01-02", "contract_date": "202401", "close": 30000},
        {"date": "2024-01-03", "contract_date": "202401", "close": 30100},
    ]
    curve, detail = bh._futures_history(rows, date(2024, 1, 1), date(2024, 1, 5),
                                        Decimal(1000000), Decimal(5), "TX")
    assert detail[0]["quantity"] == pytest.approx(5 / 6)
    assert detail[0]["position"] == pytest.approx(5 / 6)
    assert detail[1]["profit"] == pytest.approx((5 / 6) * 200 * 100)
    assert curve[1]["equity"] == pytest.approx(1000000 + (5 / 6) * 200 * 100)


def test_futures_without_known_contract_value_reports_error(monkeypatch):
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "contract_date": "202401", "close": 100},
    ], []))
    result = bh.analyze_buy_hold(source(), bh.BuyHoldSettings(
        product_type="期貨", code="UNKNOWN", amount_wan=100, leverage=5))
    assert "尚未設定每點價值" in result["error"]
    assert result["curve"] == []


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
