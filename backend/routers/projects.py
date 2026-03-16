from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from backend.models.project import ProjectCopyRequest, ProjectCreateRequest, ProjectListResponse, ProjectPatchRequest
from backend.services.project_access import (
    create_project,
    create_project_with_user,
    get_project_access,
    list_projects_for_guest,
    now_utc_iso,
    project_dir,
    touch_access_time,
    update_project,
)
from backend.db.database import get_conn

router = APIRouter(prefix="/projects", tags=["projects"])


def _cleanup_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


def _clear_dir(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def _safe_extract_zip(zip_path: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    root = dst.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename or ""
            if not name or name.endswith("/"):
                continue
            target = (dst / name).resolve()
            if root not in target.parents and target != root:
                raise HTTPException(status_code=400, detail="Invalid zip path")
        zf.extractall(dst)


@router.get("", response_model=ProjectListResponse)
def list_projects(guest_id: str = Query(..., min_length=8)):
    projects = list_projects_for_guest(guest_id)
    return {"projects": projects}


@router.post("")
def post_project(payload: ProjectCreateRequest):
    project = create_project(payload.guest_id, payload.project_name)
    return {"project_id": project["project_id"], "project": project}


@router.get("/{project_id}")
def get_project(project_id: str, guest_id: str = Query(..., min_length=8)):
    project, _ = get_project_access(project_id, guest_id)
    touch_access_time(project_id)
    return {"project": project}


@router.patch("/{project_id}")
def patch_project(project_id: str, payload: ProjectPatchRequest):
    project = update_project(project_id, payload.guest_id, payload.project_name)
    return {"project": project}


@router.delete("/{project_id}")
def delete_project(project_id: str, guest_id: str = Query(..., min_length=8)):
    project, access = get_project_access(project_id, guest_id)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete")

    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()

    shutil.rmtree(project_dir(project_id), ignore_errors=True)
    return {"deleted": True, "project_id": project_id, "project_name": project["project_name"]}


@router.post("/{project_id}/copy")
def copy_project(project_id: str, payload: ProjectCopyRequest):
    source, _ = get_project_access(project_id, payload.guest_id)

    # Copy always creates a new owner project for the caller.
    cloned = create_project_with_user(payload.guest_id, payload.project_name)
    src_dir = project_dir(project_id)
    dst_dir = project_dir(cloned["project_id"])
    if src_dir.exists():
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

    return {"project_id": cloned["project_id"], "project": cloned}


@router.get("/{project_id}/download")
def download_project(project_id: str, guest_id: str = Query(..., min_length=8)):
    get_project_access(project_id, guest_id)
    src_dir = project_dir(project_id)
    if not src_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    fd, tmp_name = tempfile.mkstemp(prefix=f"{project_id}_", suffix=".zip")
    os.close(fd)
    Path(tmp_name).unlink(missing_ok=True)
    tmp_zip = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in src_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=str(f.relative_to(src_dir)))
    except Exception:
        _cleanup_temp_file(tmp_zip)
        raise

    touch_access_time(project_id)
    return FileResponse(
        path=tmp_zip,
        media_type="application/zip",
        filename=f"{project_id}.zip",
        background=BackgroundTask(_cleanup_temp_file, tmp_zip),
    )


@router.post("/{project_id}/upload")
def upload_project_zip(
    project_id: str,
    file: UploadFile = File(...),
    project_name: str = Form(..., min_length=1),
    guest_id: str = Query(..., min_length=8),
):
    project_name = project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="project_name cannot be empty")

    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip is supported")

    # Keep API access pattern consistent with other project endpoints.
    # Existing project: allow read-only or owner; missing project: create as anonymous.
    try:
        get_project_access(project_id, guest_id)
    except HTTPException as e:
        if e.status_code != 404:
            raise

    fd, tmp_name = tempfile.mkstemp(prefix=f"{project_id}_upload_", suffix=".zip")
    os.close(fd)
    tmp_zip = Path(tmp_name)
    try:
        with tmp_zip.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        # Validate zip before mutating project directory.
        with zipfile.ZipFile(tmp_zip, "r"):
            pass
    except zipfile.BadZipFile:
        _cleanup_temp_file(tmp_zip)
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception:
        _cleanup_temp_file(tmp_zip)
        raise

    target_dir = project_dir(project_id)
    if target_dir.exists():
        _clear_dir(target_dir)
    else:
        target_dir.mkdir(parents=True, exist_ok=True)

    try:
        _safe_extract_zip(tmp_zip, target_dir)
    finally:
        _cleanup_temp_file(tmp_zip)

    ts = now_utc_iso()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE projects SET user_id = ?, project_name = ?, access_time = ? WHERE project_id = ?",
                ("anonymous", project_name, ts, project_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO projects (project_id, user_id, project_name, create_time, access_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, "anonymous", project_name, ts, ts),
            )
        conn.commit()

    touch_access_time(project_id)
    return {"ok": True, "project_id": project_id, "user_id": "anonymous", "project_name": project_name}
