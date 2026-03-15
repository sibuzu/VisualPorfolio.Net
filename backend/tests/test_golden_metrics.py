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
    for fn in ["aa-1.srp", "aa-2.srp", "aa-3.srp"]:
        path = Path("ref_result/project") / fn
        exp_net, exp_mdd = _srp_expected(path)
        trades = parse_file(path, strategy_index=0)
        merged = merge_trades([(trades, {"weight": 1, "contract": 1})], None, None)
        report = build_report(merged, risk_free_rate=3, mdd_count=5)

        assert abs(report["summary"]["net_profit"] - exp_net) < 5.0, fn
        assert abs(report["summary"]["mdd"] - exp_mdd) < 5.0, fn
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
