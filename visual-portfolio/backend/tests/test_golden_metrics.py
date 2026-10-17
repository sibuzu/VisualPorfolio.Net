from pathlib import Path
import xml.etree.ElementTree as ET

from backend.services.parser import parse_file
from backend.services.portfolio import merge_trades
from backend.services.summary_report import build_report


def _srp_expected(path: Path) -> tuple[float, float]:
    root = ET.parse(path).getroot()
    node = root.find("./策略參數/StgBDSXv5")
    if node is None:
        return 0.0, 0.0
    net = float((node.findtext("累計績效") or "0").strip())
    mdd = abs(float((node.findtext("MaxDrawdown") or "0").strip()))
    return net, mdd


def test_srp_golden_metrics_for_all_samples():
    visual_portfolio_mdd = {
        "aa-1.srp": 4379.602161,
        "aa-2.srp": 3480.928361,
        "aa-3.srp": 4497.778458,
    }
    for fn in ["aa-1.srp", "aa-2.srp", "aa-3.srp"]:
        path = Path("ref_result/project") / fn
        exp_net, _ = _srp_expected(path)
        trades = parse_file(path, strategy_index=0)
        merged = merge_trades([(trades, {"weight": 1, "contract": 1})], None, None)
        report = build_report(merged, risk_free_rate=3, mdd_count=5)

        assert abs(report["summary"]["net_profit"] - exp_net) < 5.0, fn
        assert abs(report["summary"]["mdd"] - visual_portfolio_mdd[fn]) < 1e-6, fn
        assert len(report["monthly"]) > 0, fn
        assert len(report["annual"]) > 0, fn
        assert len(report["weekly"]) > 0, fn


def test_xrp_golden_end_to_end_pnl_from_amount_qty_logic():
    path = Path("ref_result/project/Report.xrp")
    root = ET.parse(path).getroot()
    trades = root.findall("./Trades/Trade")
    assert trades

    signed_amounts = [float(t.attrib["amount"]) for t in trades if "amount" in t.attrib]
    assert len(signed_amounts) >= 2
    expected = sum(signed_amounts)

    parsed = parse_file(path, strategy_index=0)
    merged = merge_trades([(parsed, {"weight": 1, "contract": 1})], None, None)
    report = build_report(merged)

    assert abs(report["summary"]["net_profit"] - expected) < 1e-6


def test_summary_mdd_uses_last_equity_per_day():
    trades = [
        {"trade_date2": "2024-01-01 10:00:00", "net_profit": 100.0, "trade_amount": 1.0},
        {"trade_date2": "2024-01-02 10:00:00", "net_profit": -80.0, "trade_amount": 1.0},
        {"trade_date2": "2024-01-02 14:00:00", "net_profit": 60.0, "trade_amount": 1.0},
        {"trade_date2": "2024-01-03 10:00:00", "net_profit": -30.0, "trade_amount": 1.0},
    ]

    report = build_report(trades)

    assert report["summary"]["mdd"] == 50.0
    assert report["mdd_markers"][0]["value"] == -50.0


def test_summary_mdd_counts_initial_daily_loss_from_zero():
    trades = [
        {"trade_date2": "2024-01-01 10:00:00", "net_profit": -100.0, "trade_amount": 1.0},
        {"trade_date2": "2024-01-02 10:00:00", "net_profit": 50.0, "trade_amount": 1.0},
    ]

    report = build_report(trades)

    assert report["summary"]["mdd"] == 100.0
    assert report["mdd_markers"][0]["value"] == -100.0


def test_period_mdd_uses_daily_equity_not_intraday_troughs():
    trades = [
        {"trade_date2": "2026-01-01 10:00:00", "net_profit": 100.0, "trade_amount": 1.0},
        {"trade_date2": "2026-01-02 09:00:00", "net_profit": -200.0, "trade_amount": 1.0},
        {"trade_date2": "2026-01-02 13:30:00", "net_profit": 150.0, "trade_amount": 1.0},
    ]

    report = build_report(trades)

    assert report["annual"][0]["mdd"] == 50.0
    assert report["monthly"][0]["mdd"] == 50.0
    assert report["weekly"][0]["mdd"] == 50.0
