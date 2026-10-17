from __future__ import annotations

import io
from pathlib import Path
import zipfile

import pytest

import strategy_report.importer as importer
from strategy_report.importer import ReportFormatError, parse_report
from strategy_report.analysis import CalculationSettings, analyze_report

FIXTURES = Path(__file__).parent / "fixtures"


def _sea(toml: str, events: str, *, extra: dict[str, str] | None = None) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("demo/strategy.toml", toml)
        archive.writestr("demo/events.jsonl", events)
        for name, text in (extra or {}).items():
            archive.writestr(name, text)
    return out.getvalue()


def test_srp_and_sea_normalize_same_events_and_capital():
    srp = b'''<\xe7\xad\x96\xe7\x95\xa5\xe5\x9b\x9e\xe6\xb8\xac><\xe5\x8f\x83\xe6\x95\xb8>
    <\xe7\xad\x96\xe7\x95\xa5>Demo</\xe7\xad\x96\xe7\x95\xa5><\xe8\xbf\x91\xe6\x9c\x88\xe4\xbb\xa3\xe7\xa2\xbc>TXF (\xe5\x8f\xb0\xe6\x8c\x87\xe6\x9c\x9f)</\xe8\xbf\x91\xe6\x9c\x88\xe4\xbb\xa3\xe7\xa2\xbc>
    <InitCapital>8,000\xe8\x90\xac</InitCapital><\xe6\x9c\x80\xe5\xb0\x8f\xe8\xb7\xb3\xe5\x8b\x95\xe9\xbb\x9e>1</\xe6\x9c\x80\xe5\xb0\x8f\xe8\xb7\xb3\xe5\x8b\x95\xe9\xbb\x9e>
    <\xe6\x9c\x80\xe5\xb0\x8f\xe8\xb7\xb3\xe5\x8b\x95\xe9\x87\x91\xe9\xa1\x8d>200</\xe6\x9c\x80\xe5\xb0\x8f\xe8\xb7\xb3\xe5\x8b\x95\xe9\x87\x91\xe9\xa1\x8d>
    </\xe5\x8f\x83\xe6\x95\xb8><\xe7\xad\x96\xe7\x95\xa5\xe4\xba\xa4\xe6\x98\x93>
    <Trade index="1" time_stamp="2024/01/02 09:00:00" bs="B" contract="2" price="100"/>
    <Trade index="1" time_stamp="2024/01/03 09:00:00" bs="S" contract="2" price="105"/>
    </\xe7\xad\x96\xe7\x95\xa5\xe4\xba\xa4\xe6\x98\x93></\xe7\xad\x96\xe7\x95\xa5\xe5\x9b\x9e\xe6\xb8\xac>'''
    sea = _sea(
        '[strategy]\nname="Demo"\n[params]\n"策略"="Demo"\n"近月代碼"="TXF (台指期)"\n'
        '"InitCapital"="8,000萬"\n"最小跳動點"="1"\n"最小跳動金額"="200"\n',
        '{"timestamp":"2024-01-02T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":100,"quantity":2,"hedge_id":"1"}}\n'
        '{"timestamp":"2024-01-03T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":105,"quantity":-2,"hedge_id":"1"}}\n',
    )
    a = parse_report("demo.srp", srp)
    b = parse_report("demo.sea", sea)
    assert a.initial_capital == b.initial_capital == 80_000_000
    assert a.point_value == b.point_value == 200
    assert [(x.timestamp, x.side, x.quantity, x.price, x.symbol) for x in a.events] == [
        (x.timestamp, x.side, x.quantity, x.price, x.symbol) for x in b.events
    ]


@pytest.mark.parametrize("filename,payload", [
    ("x.txt", b"plain"),
    ("x.srp", b"<!DOCTYPE foo><root/>"),
    ("x.srp", b"<root/>"),
    ("x.sea", b"not a zip"),
])
def test_invalid_uploads(filename: str, payload: bytes):
    with pytest.raises(ReportFormatError):
        parse_report(filename, payload)


def test_non_finite_source_slippage_is_rejected():
    payload = ('<策略回測><參數><滑價>NaN</滑價></參數><策略交易>'
               '<Trade time_stamp="2024/01/01 09:00:00" bs="B" contract="1" price="100"/>'
               '</策略交易></策略回測>').encode()
    with pytest.raises(ReportFormatError, match="slippage"):
        parse_report("bad.srp", payload)


@pytest.mark.parametrize("trade_cost,expected_profit", [("2", 200), ("0.1%", 959)])
def test_sea_trade_cost_matches_point_or_percent_slippage(trade_cost: str, expected_profit: int):
    payload = _sea(
        '[strategy]\nname="Demo"\n[params]\n"MinPointUnit"="1"\n'
        f'"MinPointPrice"="200"\n"TradeCost"="{trade_cost}"\n',
        '{"timestamp":"2024-01-02T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":100,"quantity":1}}\n'
        '{"timestamp":"2024-01-03T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":105,"quantity":-1}}\n',
    )
    source = parse_report("demo.sea", payload)
    report = analyze_report(source, CalculationSettings(mode="backtest"))
    assert source.slippage == trade_cost
    assert report["simple"]["summary"]["trade_cost"] == trade_cost
    assert report["simple"]["summary"]["net_profit"] == expected_profit


def test_rejects_traversal_member():
    payload = _sea('[strategy]\nname="Demo"\n', '', extra={"../escape.txt": "x"})
    with pytest.raises(ReportFormatError, match="unsafe path"):
        parse_report("demo.sea", payload)


def test_rejects_size_and_entry_limits(monkeypatch):
    monkeypatch.setattr(importer, "MAX_UPLOAD_BYTES", 5)
    with pytest.raises(ReportFormatError, match="upload limit"):
        parse_report("demo.srp", b"longer than five")
    monkeypatch.setattr(importer, "MAX_UPLOAD_BYTES", 20 * 1024 * 1024)
    monkeypatch.setattr(importer, "MAX_ARCHIVE_ENTRIES", 2)
    payload = _sea('[strategy]\nname="Demo"\n', '', extra={"demo/extra.txt": "x"})
    with pytest.raises(ReportFormatError, match="too many entries"):
        parse_report("demo.sea", payload)


def test_sea_spec_paired_examples_when_available():
    root = Path("/home/jack/git/sea_spec/examples/srp")
    if not root.is_dir():
        pytest.skip("sea_spec examples are not available")
    for name, count, point_value in (
        ("BDS", 3057, 5000),
        ("BDS_BTC", 68, 1),
        ("BDS_TXF", 212, 200),
        ("TX時間沖", 6074, 200),
    ):
        folder = root / name
        srp = parse_report(f"{name}.srp", (folder / f"{name}.srp").read_bytes())
        sea_payload = _sea((folder / "strategy.toml").read_text(), (folder / "events.jsonl").read_text())
        sea = parse_report(f"{name}.sea", sea_payload)
        fields = ("timestamp", "side", "quantity", "price", "symbol", "strategy_index", "tag")
        assert len(srp.events) == len(sea.events) == count
        assert srp.point_value == sea.point_value == point_value
        assert all(all(getattr(a, field) == getattr(b, field) for field in fields)
                   for a, b in zip(srp.events, sea.events))


def test_repo_paired_fixture_is_numerically_identical():
    srp = parse_report("BDS_TXF.srp", (FIXTURES / "BDS_TXF.srp").read_bytes())
    sea = parse_report("BDS_TXF.sea", (FIXTURES / "BDS_TXF.sea").read_bytes())
    fields = ("timestamp", "side", "quantity", "price", "symbol", "strategy_index", "tag")
    assert len(srp.events) == len(sea.events) == 212
    assert all(all(getattr(a, field) == getattr(b, field) for field in fields)
               for a, b in zip(srp.events, sea.events))


@pytest.mark.parametrize("mode", [
    "backtest", "fixed_quantity", "risk_factor", "target_leverage", "profit_step",
    "fixed_amount", "fixed_risk", "profit_risk", "target_margin", "kelly",
])
def test_repo_paired_fixture_reports_match_for_every_mode(mode):
    srp = parse_report("BDS_TXF.srp", (FIXTURES / "BDS_TXF.srp").read_bytes())
    sea = parse_report("BDS_TXF.sea", (FIXTURES / "BDS_TXF.sea").read_bytes())
    settings = CalculationSettings(mode=mode, chip_size=100_000 if mode == "kelly" else 0)
    srp_report = analyze_report(srp, settings)
    sea_report = analyze_report(sea, settings)
    for section in ("simple", "compound"):
        assert srp_report[section] == sea_report[section]
