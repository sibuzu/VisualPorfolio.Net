from __future__ import annotations

import asyncio
import shutil
from datetime import datetime, timedelta, timezone

from backend.db.database import get_conn
from backend.services.project_access import project_dir


CLEANUP_INTERVAL_SECONDS = 3600


def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def cleanup_stale_projects(hours: int = 72) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    deleted = 0

    with get_conn() as conn:
        rows = conn.execute("SELECT project_id, user_id, access_time FROM projects").fetchall()
        stale_ids: list[str] = []
        for row in rows:
            if str(row["user_id"]) == "admin":
                continue
            try:
                access_time = _iso_to_dt(row["access_time"])
            except Exception:
                stale_ids.append(row["project_id"])
                continue
            if access_time < cutoff:
                stale_ids.append(row["project_id"])

        for project_id in stale_ids:
            conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            shutil.rmtree(project_dir(project_id), ignore_errors=True)
            deleted += 1
        conn.commit()

    return deleted


async def cleanup_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        cleanup_stale_projects()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=CLEANUP_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue
