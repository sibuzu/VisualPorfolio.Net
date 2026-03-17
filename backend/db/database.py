from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_DIR = DATA_DIR / "db"
DB_PATH = DB_DIR / "projects.db"


def ensure_data_dirs() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "projects").mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    ensure_data_dirs()
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                create_time TEXT NOT NULL,
                access_time TEXT NOT NULL,
                never_expires INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cols = conn.execute("PRAGMA table_info(projects)").fetchall()
        has_never_expires = any(str(c["name"]) == "never_expires" for c in cols)
        if not has_never_expires:
            conn.execute("ALTER TABLE projects ADD COLUMN never_expires INTEGER NOT NULL DEFAULT 0")
        conn.commit()


@contextmanager
def get_conn() -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
