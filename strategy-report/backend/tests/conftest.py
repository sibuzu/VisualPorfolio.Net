import pytest


@pytest.fixture(autouse=True)
def isolated_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("STRATEGY_REPORT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("STRATEGY_REPORT_REPORTS_DIR", raising=False)
    monkeypatch.delenv("STRATEGY_REPORT_LEGACY_DB", raising=False)
