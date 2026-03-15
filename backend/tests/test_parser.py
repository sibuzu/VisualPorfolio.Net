from pathlib import Path

from backend.services.parser import parse_file


def test_parse_srp_has_rows():
    rows = parse_file(Path("ref_result/project/aa-1.srp"), strategy_index=0)
    assert len(rows) > 10


def test_parse_xrp_has_rows():
    rows = parse_file(Path("ref_result/project/Report.xrp"), strategy_index=0)
    assert len(rows) > 10
