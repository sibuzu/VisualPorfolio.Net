from pathlib import Path
import io
import zipfile

from backend.services.parser import parse_file
from backend.services.sea_convert import convert_legacy_payload_to_sea


def test_parse_srp_has_rows():
    rows = parse_file(Path("ref_result/project/aa-1.srp"), strategy_index=0)
    assert len(rows) > 10


def test_parse_xrp_has_rows():
    rows = parse_file(Path("ref_result/project/Report.xrp"), strategy_index=0)
    assert len(rows) > 10


def _make_sea_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "demo/strategy.toml",
            '[params."基本設定"]\n"滑價成本" = "0"\n',
        )
        zf.writestr(
            "demo/events.jsonl",
            "\n".join(
                [
                    '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":100,"quantity":1}}',
                    '{"timestamp":"2025-01-02T00:00:00Z","type":"price","data":{"instrument_id":"SPY","price":101}}',
                    '{"timestamp":"2025-01-03T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":102,"quantity":-1}}',
                ]
            ),
        )
    return buf.getvalue()


def _make_sea_bytes_with_zero_price_close() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "demo/strategy.toml",
            '[params]\n"契約價值" = "50"\n"滑價" = "1"\n',
        )
        zf.writestr(
            "demo/events.jsonl",
            "\n".join(
                [
                    '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"TXF","price":100,"quantity":2}}',
                    '{"timestamp":"2025-01-02T00:00:00Z","type":"trade","data":{"instrument_id":"TXF","price":0,"quantity":-2}}',
                ]
            ),
        )
    return buf.getvalue()


def test_parse_sea_has_rows(tmp_path):
    sea_path = tmp_path / "demo.sea"
    sea_path.write_bytes(_make_sea_bytes())
    rows = parse_file(sea_path, strategy_index=0)
    assert len(rows) >= 2


def test_parse_sea_keeps_zero_price_trade(tmp_path):
    sea_path = tmp_path / "zero_close.sea"
    sea_path.write_bytes(_make_sea_bytes_with_zero_price_close())
    rows = parse_file(sea_path, strategy_index=0)
    assert len(rows) == 2
    assert rows[-1].price1 == 0
    assert abs(sum(x.net_profit for x in rows) + 10200.0) < 1e-6


def test_parse_sea_prefers_params_cost_when_basic_is_zero(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "demo/strategy.toml",
            "\n".join(
                [
                    '[params]',
                    '"交易成本" = "0.05%"',
                    '[params."基本設定"]',
                    '"滑價成本" = "0"',
                ]
            )
            + "\n",
        )
        zf.writestr(
            "demo/events.jsonl",
            "\n".join(
                [
                    '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":100,"quantity":1}}',
                    '{"timestamp":"2025-01-02T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":110,"quantity":-1}}',
                ]
            ),
        )
    sea_path = tmp_path / "cost_pref.sea"
    sea_path.write_bytes(buf.getvalue())
    rows = parse_file(sea_path, strategy_index=0)
    # (110-100) - 0.05%*(100+110) = 9.895
    assert abs(sum(x.net_profit for x in rows) - 9.895) < 1e-6


def test_parse_sea_always_applies_contract_value_with_large_quantity(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "demo/strategy.toml",
            "\n".join(
                [
                    "[params]",
                    '"ContractValue" = "50"',
                    '"TradeCost" = "0"',
                ]
            )
            + "\n",
        )
        zf.writestr(
            "demo/events.jsonl",
            "\n".join(
                [
                    '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"TXF","price":100,"quantity":100}}',
                    '{"timestamp":"2025-01-02T00:00:00Z","type":"trade","data":{"instrument_id":"TXF","price":110,"quantity":-100}}',
                ]
            ),
        )
    sea_path = tmp_path / "large_qty_contract_value.sea"
    sea_path.write_bytes(buf.getvalue())
    rows = parse_file(sea_path, strategy_index=0)
    assert abs(sum(x.net_profit for x in rows) - 50000.0) < 1e-6


def test_parse_gsea_has_rows(tmp_path):
    sea_bytes = _make_sea_bytes()
    gsea_path = tmp_path / "demo.gsea"
    with zipfile.ZipFile(gsea_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("demo/group.json", '{"group":[{"project":"demo","count":1,"weight":"1"}]}')
        zf.writestr("demo/demo.sea", sea_bytes)
    rows = parse_file(gsea_path, strategy_index=0)
    assert len(rows) >= 2


def test_parse_srp_missing_slippage_defaults_zero(tmp_path):
    srp = """<?xml version="1.0" encoding="utf-8"?>
<策略回測>
  <參數>
    <最小跳動點>1</最小跳動點>
    <最小跳動金額>1</最小跳動金額>
  </參數>
  <策略交易>
    <Trade index="1" bs="B" contract="1" price="100" time_stamp="2025/01/01 00:00:00" />
    <Trade index="1" bs="S" contract="1" price="110" time_stamp="2025/01/02 00:00:00" />
  </策略交易>
</策略回測>
"""
    p = tmp_path / "no_slip.srp"
    p.write_text(srp, encoding="utf-8")
    rows = parse_file(p, strategy_index=0)
    assert abs(sum(x.net_profit for x in rows) - 10.0) < 1e-6


def test_convert_srp_does_not_inject_slippage_fields():
    srp = """<?xml version="1.0" encoding="utf-8"?>
<策略回測>
  <參數>
    <策略>Demo</策略>
    <最小跳動點>1</最小跳動點>
    <最小跳動金額>1</最小跳動金額>
  </參數>
  <策略參數>
    <StgDemo>
      <策略名稱>Demo</策略名稱>
    </StgDemo>
  </策略參數>
  <策略交易>
    <Trade index="1" bs="B" contract="1" price="100" time_stamp="2025/01/01 00:00:00" />
    <Trade index="1" bs="S" contract="1" price="110" time_stamp="2025/01/02 00:00:00" />
  </策略交易>
</策略回測>
"""
    _, payload = convert_legacy_payload_to_sea("demo.srp", srp.encode("utf-8"))
    with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
        strategy = [n for n in zf.namelist() if n.endswith("/strategy.toml")][0]
        text = zf.read(strategy).decode("utf-8")
    assert '"滑價"' not in text
    assert '"滑價成本"' not in text


def test_convert_srp_keeps_defined_slippage_fields():
    srp = """<?xml version="1.0" encoding="utf-8"?>
<策略回測>
  <參數>
    <策略>Demo</策略>
    <滑價>1</滑價>
    <契約價值>50</契約價值>
    <最小跳動點>1</最小跳動點>
    <最小跳動金額>50</最小跳動金額>
  </參數>
  <策略參數>
    <StgDemo>
      <策略名稱>Demo</策略名稱>
    </StgDemo>
  </策略參數>
  <策略交易>
    <Trade index="1" bs="B" contract="1" price="100" time_stamp="2025/01/01 00:00:00" />
    <Trade index="1" bs="S" contract="1" price="110" time_stamp="2025/01/02 00:00:00" />
  </策略交易>
</策略回測>
"""
    _, payload = convert_legacy_payload_to_sea("demo.srp", srp.encode("utf-8"))
    with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
        strategy = [n for n in zf.namelist() if n.endswith("/strategy.toml")][0]
        text = zf.read(strategy).decode("utf-8")
    assert '"契約價值" = "50"' in text
    assert '"滑價" = "1"' in text
    assert '"滑價成本"' not in text
