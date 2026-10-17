from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from strategy_report.analysis import CalculationSettings
from strategy_report.importer import parse_report
import strategy_report.storage as storage


FIXTURES = Path(__file__).parent / "fixtures"


def test_configured_data_directory_works_with_container_module_path(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "__file__", "/app/strategy_report/storage.py")
    storage.initialize_storage()
    assert (tmp_path / "db" / "reporsts.db").is_file()


def seed_database(tmp_path, reports):
    records = []
    with sqlite3.connect(tmp_path / "performances.db") as connection:
        connection.execute("""
            CREATE TABLE performances (
                performance_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, file_hash TEXT NOT NULL,
                name TEXT NOT NULL, strategy_name TEXT NOT NULL, filename TEXT NOT NULL,
                source_format TEXT NOT NULL, settings_json TEXT NOT NULL, important INTEGER NOT NULL,
                created_at TEXT NOT NULL, accessed_at TEXT NOT NULL)
        """)
        for extension in ("srp", "sea"):
            filename = f"BDS_TXF.{extension}"
            content = (FIXTURES / filename).read_bytes()
            item_id = storage.performance_id(content)
            path = reports / item_id / f"source.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            settings = CalculationSettings(initial_capital=345678, mode="fixed_quantity",
                                           date_start="2024-01-01", date_end="2024-12-31")
            connection.execute("INSERT INTO performances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (item_id, "owner", sha256(content).hexdigest(), "原有績效", "Strategy",
                                filename, extension, settings.model_dump_json(), 1,
                                "2026-10-14", "2026-10-15"))
            records.append((item_id, content))
    return records


def test_settings_migration_preserves_metadata_and_deleted_records_stay_deleted(monkeypatch, tmp_path):
    reports = tmp_path / "mounted-reports"
    monkeypatch.setenv("STRATEGY_REPORT_REPORTS_DIR", str(reports))
    records = seed_database(tmp_path, reports)
    storage.initialize_storage()
    assert (tmp_path / "db" / "reporsts.db").exists()
    assert (tmp_path / "db" / "reporsts.db.before-config-json").exists()
    for item_id, content in records:
        config = json.loads((reports / item_id / "config.json").read_text())
        item, restored = storage.get_performance("owner", item_id, include_content=True)
        assert item["owner_id"] == "owner" and item["name"] == "原有績效"
        assert item["important"] is True and item["created_at"] == "2026-10-14"
        assert item["accessed_at"] == "2026-10-15"
        assert config["initial_capital"] == "345678"
        assert config["date_start"] == "2024-01-01" and config["date_end"] == "2024-12-31"
        assert "owner_id" not in config and "name" not in config
        assert restored == content
    with sqlite3.connect(tmp_path / "db" / "reporsts.db") as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(performances)")}
        assert "settings_json" not in columns and "owner_id" in columns
    with sqlite3.connect(tmp_path / "db" / "reporsts.db.before-config-json") as connection:
        assert connection.execute("SELECT count(settings_json) FROM performances").fetchone()[0] == 2
    storage.delete_performance("owner", records[0][0])
    storage.initialize_storage()
    assert [item["performance_id"] for item in storage.list_performances("owner")] == [records[1][0]]


def test_interrupted_migration_can_resume_without_overwriting_configs(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    records = seed_database(tmp_path, reports)
    write_settings = storage._write_settings

    def fail_second(item_id, settings):
        if item_id == records[1][0]:
            raise OSError("disk unavailable")
        write_settings(item_id, settings)

    monkeypatch.setattr(storage, "_write_settings", fail_second)
    with pytest.raises(OSError, match="disk unavailable"):
        storage.initialize_storage()
    assert (tmp_path / "db" / "reporsts.db").exists()
    first_config = reports / records[0][0] / "config.json"
    first_bytes = first_config.read_bytes()
    monkeypatch.setattr(storage, "_write_settings", write_settings)
    storage.initialize_storage()
    assert first_config.read_bytes() == first_bytes
    assert len(storage.list_performances("owner")) == 2
    with sqlite3.connect(tmp_path / "db" / "reporsts.db") as connection:
        assert "settings_json" not in {row[1] for row in connection.execute("PRAGMA table_info(performances)")}


def test_concurrent_uploads_and_copies_have_independent_configs(tmp_path):
    payload = (FIXTURES / "BDS_TXF.srp").read_bytes()
    source = parse_report("BDS_TXF.srp", payload)
    with ThreadPoolExecutor(max_workers=4) as pool:
        uploaded = list(pool.map(lambda _: storage.create_performance("owner", payload, source, "策略"), range(8)))
    assert sum(created for _, created in uploaded) == 1
    item_id = uploaded[0][0]["performance_id"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        copies = list(pool.map(lambda _: storage.copy_performance("viewer", item_id), range(8)))
    assert len({copy["performance_id"] for copy in copies}) == 8
    for copy in copies:
        assert copy["performance_id"] != item_id and copy["owner_id"] == "viewer"
        assert (tmp_path / "reports" / copy["performance_id"] / "config.json").is_file()
    storage.save_settings("viewer", copies[0]["performance_id"], CalculationSettings(initial_capital=999999))
    assert storage.get_performance("owner", item_id)[0]["settings"]["initial_capital"] != "999999"
    assert storage.get_performance("viewer", copies[1]["performance_id"])[0]["settings"]["initial_capital"] != "999999"


def test_failed_config_write_preserves_previous_settings(monkeypatch, tmp_path):
    payload = (FIXTURES / "BDS_TXF.srp").read_bytes()
    item, _ = storage.create_performance("owner", payload, parse_report("report.srp", payload), "策略")
    config_path = tmp_path / "reports" / item["performance_id"] / "config.json"
    before = config_path.read_bytes()

    def fail_replace(*args):
        raise OSError("replace failed")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        storage.save_settings("owner", item["performance_id"], CalculationSettings(initial_capital=777777))
    assert config_path.read_bytes() == before
    assert not list(config_path.parent.glob("*.tmp"))


def test_relocate_read_only_database_without_overwriting_existing_index(monkeypatch, tmp_path):
    records = seed_database(tmp_path, tmp_path / "reports")
    storage.initialize_storage()
    target = tmp_path / "db" / "reporsts.db"
    legacy = tmp_path / "legacy-volume" / "performances.db"
    legacy.parent.mkdir()
    target.rename(legacy)
    legacy.chmod(0o444)
    before = legacy.read_bytes()
    monkeypatch.setenv("STRATEGY_REPORT_LEGACY_DB", str(legacy))
    storage.initialize_storage()
    assert target.is_file() and len(storage.list_performances("owner")) == 2
    storage.update_performance("owner", records[0][0], name="搬移後名稱")
    storage.initialize_storage()
    assert storage.get_performance("owner", records[0][0])[0]["name"] == "搬移後名稱"
    assert legacy.read_bytes() == before
