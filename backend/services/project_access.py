from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from backend.db.database import DATA_DIR, get_conn
from backend.services.idgen import new_project_id


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_bool(value: int | bool) -> bool:
    return bool(value)


def row_to_project(row) -> dict:
    return {
        "project_id": row["project_id"],
        "user_id": row["user_id"],
        "project_name": row["project_name"],
        "shared": parse_bool(row["shared"]),
        "create_time": datetime.fromisoformat(row["create_time"]),
        "access_time": datetime.fromisoformat(row["access_time"]),
    }


def generate_unique_project_id() -> str:
    with get_conn() as conn:
        while True:
            candidate = new_project_id()
            row = conn.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", (candidate,)
            ).fetchone()
            if not row:
                return candidate


def project_dir(project_id: str) -> Path:
    return DATA_DIR / "projects" / project_id


def create_project(guest_id: str, project_name: str) -> dict:
    project_id = generate_unique_project_id()
    ts = now_utc_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO projects (project_id, user_id, project_name, shared, create_time, access_time)
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (project_id, guest_id, project_name.strip(), ts, ts),
        )
        conn.commit()
    project_dir(project_id).mkdir(parents=True, exist_ok=True)
    return get_project(project_id)


def list_projects_for_guest(guest_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM projects
            WHERE user_id = ?
            ORDER BY access_time DESC
            """,
            (guest_id,),
        ).fetchall()
    return [row_to_project(r) for r in rows]


def get_project(project_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE project_id = ?", (project_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return row_to_project(row)


def get_project_access(project_id: str, guest_id: str) -> tuple[dict, str]:
    project = get_project(project_id)
    if project["user_id"] == guest_id:
        return project, "owner"
    if project["shared"]:
        return project, "read_only"
    raise HTTPException(status_code=403, detail="No access")


def touch_access_time(project_id: str) -> None:
    ts = now_utc_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET access_time = ? WHERE project_id = ?",
            (ts, project_id),
        )
        conn.commit()


def update_project(project_id: str, guest_id: str, project_name: str | None, shared: bool | None) -> dict:
    project, access = get_project_access(project_id, guest_id)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    new_name = project_name.strip() if isinstance(project_name, str) else project["project_name"]
    new_shared = int(shared if shared is not None else project["shared"])

    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET project_name = ?, shared = ?, access_time = ? WHERE project_id = ?",
            (new_name, new_shared, now_utc_iso(), project_id),
        )
        conn.commit()
    return get_project(project_id)
