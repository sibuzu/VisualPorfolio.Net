from __future__ import annotations

import shutil
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from backend.db.database import get_conn
from backend.services.auth import USERS_DB_PATH, require_admin
from backend.services.project_access import now_utc_iso, project_dir, write_project_config

router = APIRouter(prefix="/admin", tags=["admin"])
DEMO_PROJECT_ID = "VP-ZDEMOZ"
DEMO_PROJECT_NAME = "DEMO"
DEMO_USER_ID = "admin"


def _users_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/projects")
def admin_list_projects(_: bool = Depends(require_admin)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT project_id, user_id, project_name, create_time, access_time FROM projects ORDER BY access_time DESC"
        ).fetchall()
    projects = [dict(r) for r in rows]
    return {"projects": projects}


@router.delete("/projects/{project_id}")
def admin_delete_project(project_id: str, _: bool = Depends(require_admin)):
    with get_conn() as conn:
        row = conn.execute("SELECT project_id, project_name FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()
    shutil.rmtree(project_dir(project_id), ignore_errors=True)
    return {"ok": True, "project_id": project_id, "project_name": row["project_name"]}


@router.post("/projects/{project_id}/set-demo")
def admin_set_demo(project_id: str, _: bool = Depends(require_admin)):
    with get_conn() as conn:
        src = conn.execute(
            "SELECT project_id, project_name FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not src:
            raise HTTPException(status_code=404, detail="Project not found")

    src_dir = project_dir(project_id)
    dst_dir = project_dir(DEMO_PROJECT_ID)

    if project_id != DEMO_PROJECT_ID:
        shutil.rmtree(dst_dir, ignore_errors=True)
        if src_dir.exists():
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
    else:
        dst_dir.mkdir(parents=True, exist_ok=True)

    write_project_config(DEMO_PROJECT_ID, DEMO_PROJECT_NAME, DEMO_USER_ID)

    ts = now_utc_iso()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT project_id FROM projects WHERE project_id = ?",
            (DEMO_PROJECT_ID,),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE projects
                SET user_id = ?, project_name = ?, create_time = ?, access_time = ?
                WHERE project_id = ?
                """,
                (DEMO_USER_ID, DEMO_PROJECT_NAME, ts, ts, DEMO_PROJECT_ID),
            )
        else:
            conn.execute(
                """
                INSERT INTO projects (project_id, user_id, project_name, create_time, access_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (DEMO_PROJECT_ID, DEMO_USER_ID, DEMO_PROJECT_NAME, ts, ts),
            )
        conn.commit()

    return {
        "ok": True,
        "source_project_id": project_id,
        "project_id": DEMO_PROJECT_ID,
        "project_name": DEMO_PROJECT_NAME,
        "user_id": DEMO_USER_ID,
    }


@router.get("/users")
def admin_list_users(_: bool = Depends(require_admin)):
    with _users_conn() as conn:
        user_rows = conn.execute("SELECT user, access_time FROM users ORDER BY access_time DESC").fetchall()
    with get_conn() as conn:
        project_rows = conn.execute(
            "SELECT project_id, user_id, project_name, access_time FROM projects ORDER BY access_time DESC"
        ).fetchall()

    projects_by_user = {}
    for p in project_rows:
        projects_by_user.setdefault(p["user_id"], []).append(
            {
                "project_id": p["project_id"],
                "project_name": p["project_name"],
                "access_time": p["access_time"],
            }
        )

    users = []
    seen = set()
    for u in user_rows:
        uid = u["user"]
        seen.add(uid)
        users.append(
            {
                "user_id": uid,
                "access_time": u["access_time"],
                "projects": projects_by_user.get(uid, []),
            }
        )

    for uid, plist in projects_by_user.items():
        if uid in seen:
            continue
        users.append({"user_id": uid, "access_time": "", "projects": plist})

    return {"users": users}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: str, _: bool = Depends(require_admin)):
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete reserved admin user")

    with get_conn() as conn:
        rows = conn.execute("SELECT project_id FROM projects WHERE user_id = ?", (user_id,)).fetchall()
        project_ids = [r["project_id"] for r in rows]
        conn.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
        conn.commit()

    for pid in project_ids:
        shutil.rmtree(project_dir(pid), ignore_errors=True)

    with _users_conn() as conn:
        conn.execute("DELETE FROM users WHERE user = ?", (user_id,))
        conn.commit()

    return {"ok": True, "user_id": user_id, "deleted_projects": len(project_ids)}
