from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import string

from fastapi import HTTPException

from .analysis import CalculationSettings
from .model import ReportSource


ID_PATTERN = re.compile(r"^SR-[A-Z]{6}$")
PUBLIC_COLUMNS = "performance_id, owner_id, name, strategy_name, filename, source_format, important, created_at, accessed_at"


def _data_dir() -> Path:
    folder = Path(os.getenv("STRATEGY_REPORT_DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _reports_dir() -> Path:
    configured = os.getenv("STRATEGY_REPORT_REPORTS_DIR")
    if configured:
        return Path(configured)
    if os.getenv("STRATEGY_REPORT_DATA_DIR"):
        return _data_dir() / "reports"
    return Path(__file__).resolve().parents[3] / "data" / "reports"


def _report_path(item_id: str, source_format: str) -> Path:
    return _reports_dir() / item_id / f"source.{source_format}"


def _write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_report(item_id: str, source_format: str, content: bytes) -> None:
    _write_atomic(_report_path(item_id, source_format), content)


def _write_settings(item_id: str, settings: CalculationSettings) -> None:
    path = _reports_dir() / item_id / "config.json"
    _write_atomic(path, (settings.model_dump_json(indent=2) + "\n").encode("utf-8"))


def _read_settings(item_id: str) -> CalculationSettings:
    path = _reports_dir() / item_id / "config.json"
    try:
        return CalculationSettings.model_validate_json(path.read_bytes())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Saved performance settings are missing") from exc


def _migrate_settings(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(performances)")}
    if "settings_json" not in columns:
        return
    for row in connection.execute("SELECT performance_id, settings_json FROM performances"):
        item_id = row["performance_id"]
        if not (_reports_dir() / item_id / "config.json").exists():
            _write_settings(item_id, CalculationSettings.model_validate_json(row["settings_json"]))
        _read_settings(item_id)
    # Remove the old field only after all settings have been exported and read back.
    connection.execute("ALTER TABLE performances DROP COLUMN settings_json")


def _schema(connection: sqlite3.Connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS performances (
            performance_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            source_format TEXT NOT NULL,
            important INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            accessed_at TEXT NOT NULL
        )
    """)
    connection.execute("CREATE INDEX IF NOT EXISTS performances_owner_idx ON performances(owner_id, accessed_at DESC)")


def _random_id(used_ids: set[str]) -> str:
    while True:
        candidate = "SR-" + "".join(secrets.choice(string.ascii_uppercase) for _ in range(6))
        if candidate not in used_ids:
            return candidate


def _migrate_legacy(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(performances)")}
    if "content" not in columns:
        _schema(connection)
        return
    old_rows = connection.execute("SELECT * FROM performances ORDER BY created_at, user_id").fetchall()
    connection.execute("ALTER TABLE performances RENAME TO performances_legacy")
    _schema(connection)
    used_ids: set[str] = set()
    for row in old_rows:
        item_id = row["performance_id"]
        if item_id in used_ids:
            item_id = _random_id(used_ids)
        _write_report(item_id, row["source_format"], bytes(row["content"]))
        _write_settings(item_id, CalculationSettings.model_validate_json(row["settings_json"]))
        connection.execute("""
            INSERT INTO performances (performance_id, owner_id, file_hash, name, strategy_name,
                filename, source_format, important, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, row["user_id"], row["file_hash"], row["name"], row["strategy_name"],
              row["filename"], row["source_format"], row["important"],
              row["created_at"], row["accessed_at"]))
        used_ids.add(item_id)
    connection.execute("DROP TABLE performances_legacy")


@contextmanager
def _connect():
    database = _data_dir() / "performances.db"
    connection = sqlite3.connect(database, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE")
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(performances)")}
        backup_path = database.with_name("performances.db.before-config-json")
        if "settings_json" in columns and not backup_path.exists():
            # Read through a separate connection before any schema writes; keep a
            # complete pre-migration database for rollback.
            source = sqlite3.connect(database)
            backup = sqlite3.connect(backup_path)
            try:
                source.backup(backup)
            except Exception:
                backup_path.unlink(missing_ok=True)
                raise
            finally:
                backup.close()
                source.close()
        _migrate_legacy(connection)
        _migrate_settings(connection)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_storage() -> None:
    with _connect():
        pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def performance_id(content: bytes) -> str:
    number = int.from_bytes(sha256(content).digest(), "big") % (26 ** 6)
    letters = []
    for _ in range(6):
        number, remainder = divmod(number, 26)
        letters.append(chr(ord("A") + remainder))
    return "SR-" + "".join(reversed(letters))


def _public(row: sqlite3.Row, user_id: str) -> dict:
    return {
        "performance_id": row["performance_id"],
        "owner_id": row["owner_id"],
        "is_owner": row["owner_id"] == user_id,
        "name": row["name"],
        "strategy_name": row["strategy_name"],
        "filename": row["filename"],
        "source_format": row["source_format"],
        "settings": _read_settings(row["performance_id"]).model_dump(mode="json"),
        "important": bool(row["important"]),
        "created_at": row["created_at"],
        "accessed_at": row["accessed_at"],
    }


def list_performances(user_id: str) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE owner_id = ? ORDER BY accessed_at DESC, created_at DESC",
            (user_id,),
        ).fetchall()
        return [_public(row, user_id) for row in rows]


def list_important_performances(user_id: str) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE important = 1 ORDER BY accessed_at DESC, created_at DESC"
        ).fetchall()
        return [_public(row, user_id) for row in rows]


def create_performance(user_id: str, content: bytes, source: ReportSource, name: str) -> tuple[dict, bool]:
    file_hash = sha256(content).hexdigest()
    item_id = performance_id(content)
    display_name = name.strip() or source.strategy.strip() or "未命名績效"
    if len(display_name) > 160:
        raise HTTPException(status_code=422, detail="Performance name exceeds 160 characters")
    with _connect() as connection:
        existing = connection.execute(
            f"SELECT {PUBLIC_COLUMNS}, file_hash FROM performances WHERE performance_id = ?", (item_id,)
        ).fetchone()
        if existing:
            if existing["file_hash"] != file_hash:
                raise HTTPException(status_code=409, detail="Performance ID collision for different files")
            return _public(existing, user_id), False
        _write_report(item_id, source.source_format, content)
        _write_settings(item_id, CalculationSettings())
        timestamp = _now()
        connection.execute("""
            INSERT INTO performances (performance_id, owner_id, file_hash, name, strategy_name,
                filename, source_format, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, user_id, file_hash, display_name, source.strategy, source.filename,
              source.source_format, timestamp, timestamp))
        row = connection.execute(f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE performance_id = ?", (item_id,)).fetchone()
        return _public(row, user_id), True


def get_performance(user_id: str, item_id: str, *, include_content: bool = False) -> tuple[dict, bytes | None]:
    if not ID_PATTERN.fullmatch(item_id):
        raise HTTPException(status_code=404, detail="Performance not found")
    with _connect() as connection:
        row = connection.execute(f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE performance_id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Performance not found")
        content = None
        if include_content:
            try:
                content = _report_path(item_id, row["source_format"]).read_bytes()
            except FileNotFoundError as exc:
                raise HTTPException(status_code=500, detail="Saved report file is missing") from exc
        return _public(row, user_id), content


def copy_performance(user_id: str, item_id: str, name: str | None = None) -> dict:
    if not ID_PATTERN.fullmatch(item_id):
        raise HTTPException(status_code=404, detail="Performance not found")
    with _connect() as connection:
        row = connection.execute(f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE performance_id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Performance not found")
        source = _public(row, user_id)
        try:
            content = _report_path(item_id, source["source_format"]).read_bytes()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail="Saved report file is missing") from exc
        display_name = (name if name is not None else f'{source["name"]} 副本').strip()
        if not display_name or len(display_name) > 160:
            raise HTTPException(status_code=422, detail="Performance name must be 1-160 characters")
        used_ids = {row[0] for row in connection.execute("SELECT performance_id FROM performances")}
        used_ids.update(path.name for path in _reports_dir().iterdir())
        copy_id = _random_id(used_ids)
        _write_report(copy_id, source["source_format"], content)
        _write_settings(copy_id, CalculationSettings.model_validate(source["settings"]))
        timestamp = _now()
        connection.execute("""
            INSERT INTO performances (performance_id, owner_id, file_hash, name, strategy_name,
                filename, source_format, important, created_at, accessed_at)
            SELECT ?, ?, file_hash, ?, strategy_name, filename, source_format, 0, ?, ?
            FROM performances WHERE performance_id = ?
        """, (copy_id, user_id, display_name, timestamp, timestamp, item_id))
        row = connection.execute(f"SELECT {PUBLIC_COLUMNS} FROM performances WHERE performance_id = ?", (copy_id,)).fetchone()
        return _public(row, user_id)


def update_performance(user_id: str, item_id: str, *, name: str | None = None, important: bool | None = None) -> dict:
    current, _ = get_performance(user_id, item_id)
    if not current["is_owner"]:
        raise HTTPException(status_code=403, detail="Only owner can edit performance")
    display_name = current["name"] if name is None else name.strip()
    if not display_name or len(display_name) > 160:
        raise HTTPException(status_code=422, detail="Performance name must be 1-160 characters")
    starred = current["important"] if important is None else important
    with _connect() as connection:
        connection.execute("UPDATE performances SET name = ?, important = ? WHERE performance_id = ?",
                           (display_name, int(starred), item_id))
    updated, _ = get_performance(user_id, item_id)
    return updated


def save_settings(user_id: str, item_id: str, settings: CalculationSettings) -> None:
    with _connect() as connection:
        row = connection.execute("SELECT owner_id FROM performances WHERE performance_id = ?", (item_id,)).fetchone()
        if row and row["owner_id"] == user_id:
            _write_settings(item_id, settings)
            connection.execute("UPDATE performances SET accessed_at = ? WHERE performance_id = ?", (_now(), item_id))


def delete_performance(user_id: str, item_id: str) -> None:
    current, _ = get_performance(user_id, item_id)
    if not current["is_owner"]:
        raise HTTPException(status_code=403, detail="Only owner can delete performance")
    with _connect() as connection:
        connection.execute("DELETE FROM performances WHERE performance_id = ?", (item_id,))
    shutil.rmtree(_report_path(item_id, current["source_format"]).parent, ignore_errors=True)
