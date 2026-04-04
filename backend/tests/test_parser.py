from pathlib import Path
import io
import zipfile

from backend.services.parser import parse_file


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


def test_parse_sea_has_rows(tmp_path):
    sea_path = tmp_path / "demo.sea"
    sea_path.write_bytes(_make_sea_bytes())
    rows = parse_file(sea_path, strategy_index=0)
    assert len(rows) >= 2


def test_parse_gsea_has_rows(tmp_path):
    sea_bytes = _make_sea_bytes()
    gsea_path = tmp_path / "demo.gsea"
    with zipfile.ZipFile(gsea_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("demo/group.json", '{"group":[{"project":"demo","count":1,"weight":"1"}]}')
        zf.writestr("demo/demo.sea", sea_bytes)
    rows = parse_file(gsea_path, strategy_index=0)
    assert len(rows) >= 2
