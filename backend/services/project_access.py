from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import HTTPException

from backend.db.database import DATA_DIR, get_conn
from backend.services.idgen import new_project_id


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_project(row) -> dict:
    return {
        "project_id": row["project_id"],
        "user_id": row["user_id"],
        "project_name": row["project_name"],
        "create_time": datetime.fromisoformat(row["create_time"]),
        "access_time": datetime.fromisoformat(row["access_time"]),
        "never_expires": bool(row["never_expires"]) if "never_expires" in row.keys() else False,
        "important": bool(row["important"]) if "important" in row.keys() else False,
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


def write_project_config(project_id: str, project_name: str, user_id: str) -> None:
    pdir = project_dir(project_id)
    pdir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(pdir, 0o775)
    except OSError:
        pass

    cfg = pdir / "strategy.toml"
    try:
        if cfg.exists():
            try:
                os.chmod(cfg, 0o664)
            except OSError:
                pass
        cfg.write_text(_render_project_strategy_toml(project_id, project_name, user_id), encoding="utf-8")
        # Keep backward compatibility cleanup: remove legacy config.json if present.
        legacy = pdir / "config.json"
        if legacy.exists():
            legacy.unlink(missing_ok=True)
    except PermissionError:
        raise HTTPException(status_code=500, detail=f"Project config is not writable: {project_id}")


def _toml_string(value: str) -> str:
    text = str(value or "")
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _render_project_strategy_toml(project_id: str, project_name: str, user_id: str) -> str:
    return (
        "[strategy]\n"
        'type = "group"\n'
        f"name = {_toml_string(project_name)}\n"
        'project = "sea"\n'
        f"strategy_id = {_toml_string(project_id)}\n"
        f"user_id = {_toml_string(user_id)}\n"
    )


def create_project(user_id: str, project_name: str) -> dict:
    project_id = generate_unique_project_id()
    ts = now_utc_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO projects (project_id, user_id, project_name, create_time, access_time, never_expires)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (project_id, user_id, project_name.strip(), ts, ts),
        )
        conn.commit()
    project_dir(project_id).mkdir(parents=True, exist_ok=True)
    write_project_config(project_id, project_name.strip(), user_id)
    return get_project(project_id)


def list_projects_for_guest(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM projects
            WHERE user_id = ? OR user_id = 'anonymous'
            ORDER BY access_time DESC
            """,
            (user_id,),
        ).fetchall()
    return [row_to_project(r) for r in rows]


def list_important_projects() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM projects
            WHERE important = 1
            ORDER BY access_time DESC
            """
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


def get_project_access(project_id: str, user_id: str) -> tuple[dict, str]:
    project = get_project(project_id)
    if project["user_id"] == user_id:
        return project, "owner"
    return project, "read_only"


def touch_access_time(project_id: str) -> None:
    ts = now_utc_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET access_time = ? WHERE project_id = ?",
            (ts, project_id),
        )
        conn.commit()


def update_project(
    project_id: str,
    user_id: str,
    project_name: str | None,
    never_expires: bool | None = None,
    important: bool | None = None,
) -> dict:
    project, access = get_project_access(project_id, user_id)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    new_name = project_name.strip() if isinstance(project_name, str) else project["project_name"]

    new_never_expires = project["never_expires"] if never_expires is None else bool(never_expires)
    new_important = project["important"] if important is None else bool(important)

    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET project_name = ?, never_expires = ?, important = ?, access_time = ? WHERE project_id = ?",
            (new_name, 1 if new_never_expires else 0, 1 if new_important else 0, now_utc_iso(), project_id),
        )
        conn.commit()
    # Best-effort sync to strategy.toml: project rename must not fail if file permission is broken.
    try:
        write_project_config(project_id, new_name, project["user_id"])
    except HTTPException:
        pass
    return get_project(project_id)


def create_project_with_user(user_id: str, project_name: str) -> dict:
    project_id = generate_unique_project_id()
    ts = now_utc_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO projects (project_id, user_id, project_name, create_time, access_time, never_expires)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (project_id, user_id, project_name.strip(), ts, ts),
        )
        conn.commit()
    project_dir(project_id).mkdir(parents=True, exist_ok=True)
    write_project_config(project_id, project_name.strip(), user_id)
    return get_project(project_id)
