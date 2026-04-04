from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

from backend.models.project import ProjectCopyRequest, ProjectCreateRequest, ProjectListResponse, ProjectPatchRequest
from backend.services.auth import require_auth
from backend.services.project_access import (
    create_project,
    create_project_with_user,
    get_project as get_project_record,
    get_project_access,
    list_important_projects,
    list_projects_for_guest,
    now_utc_iso,
    project_dir,
    touch_access_time,
    update_project,
    write_project_config,
)
from backend.db.database import get_conn

router = APIRouter(prefix="/projects", tags=["projects"])
_og_logger = logging.getLogger("uvicorn.error")


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
        members: list[tuple[zipfile.ZipInfo, list[str]]] = []
        first_parts: list[str] = []
        for member in zf.infolist():
            raw_name = member.filename or ""
            if not raw_name:
                continue
            # Normalize Windows-style separators inside zip entries.
            normalized = raw_name.replace("\\", "/")
            parts = [p for p in normalized.split("/") if p not in {"", "."}]
            if not parts:
                continue
            if any(p == ".." for p in parts):
                raise HTTPException(status_code=400, detail="Invalid zip path")
            members.append((member, parts))
            first_parts.append(parts[0])

        strip_root = bool(first_parts) and all(p == first_parts[0] for p in first_parts)

        for member, parts in members:
            effective_parts = parts[1:] if strip_root and len(parts) >= 2 else parts
            if not effective_parts:
                continue
            rel_name = "/".join(effective_parts)

            target = (dst / rel_name).resolve()
            if root not in target.parents and target != root:
                raise HTTPException(status_code=400, detail="Invalid zip path")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)


@router.get("", response_model=ProjectListResponse)
def list_projects(current_user: str = Depends(require_auth)):
    projects = list_projects_for_guest(current_user)
    return {"projects": projects}


@router.get("/important", response_model=ProjectListResponse)
def important_projects(current_user: str = Depends(require_auth)):
    _ = current_user
    projects = list_important_projects()
    return {"projects": projects}


@router.post("")
def post_project(payload: ProjectCreateRequest, current_user: str = Depends(require_auth)):
    if current_user == "guest":
        raise HTTPException(status_code=403, detail="guest cannot create project")
    project = create_project(current_user, payload.project_name)
    return {"project_id": project["project_id"], "project": project}


@router.get("/{project_id}")
def get_project(project_id: str, current_user: str = Depends(require_auth)):
    project, _ = get_project_access(project_id, current_user)
    touch_access_time(project_id)
    return {"project": project}


@router.get("/{project_id}/og-preview", response_class=HTMLResponse)
def og_preview(project_id: str, request: Request):
    """Return an HTML page with Open Graph meta tags for social media crawlers (Line, FB, etc.).
    Real browsers are immediately redirected back to the SPA via JavaScript.
    """
    try:
        project = get_project_record(project_id)
        project_name = project["project_name"]
    except HTTPException:
        project_name = "VisualPortfolio.Net"

    site_url = "https://visualportfolio.sibuzu.com"
    page_url = f"{site_url}/projects/{project_id}"
    description = f"VisualPortfolio.Net - {project_name}"
    ua = request.headers.get("user-agent", "")
    xff = request.headers.get("x-forwarded-for", "")
    host = request.headers.get("host", "")
    _og_logger.info(
        "og-preview hit project_id=%s project_name=%s host=%s ua=%s xff=%s",
        project_id,
        project_name,
        host,
        ua,
        xff,
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <meta name="description" content="{description}" />
    <!-- Open Graph -->
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{page_url}" />
    <meta property="og:title" content="{project_name}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:site_name" content="VisualPortfolio.Net" />
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="{project_name}" />
    <meta name="twitter:description" content="{description}" />
    <!-- Redirect real browsers back to SPA -->
    <script>window.location.replace("{page_url}");</script>
  </head>
  <body>
    <p>Redirecting to <a href="{page_url}">{project_name}</a>…</p>
  </body>
</html>"""
    return HTMLResponse(content=html)


@router.patch("/{project_id}")
def patch_project(project_id: str, payload: ProjectPatchRequest, current_user: str = Depends(require_auth)):
    project = update_project(
        project_id,
        current_user,
        payload.project_name,
        payload.never_expires,
        payload.important,
    )
    return {"project": project}


@router.delete("/{project_id}")
def delete_project(project_id: str, current_user: str = Depends(require_auth)):
    project, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete")

    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()

    shutil.rmtree(project_dir(project_id), ignore_errors=True)
    return {"deleted": True, "project_id": project_id, "project_name": project["project_name"]}


@router.post("/{project_id}/copy")
def copy_project(project_id: str, payload: ProjectCopyRequest, current_user: str = Depends(require_auth)):
    if current_user == "guest":
        raise HTTPException(status_code=403, detail="guest cannot clone project")
    source, _ = get_project_access(project_id, current_user)

    # Copy always creates a new owner project for the caller.
    cloned = create_project_with_user(current_user, payload.project_name)
    src_dir = project_dir(project_id)
    dst_dir = project_dir(cloned["project_id"])
    if src_dir.exists():
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    write_project_config(cloned["project_id"], cloned["project_name"], cloned["user_id"])

    return {"project_id": cloned["project_id"], "project": cloned}


@router.get("/{project_id}/download")
def download_project(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)

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
        filename=f"{project_id}.gsea",
        background=BackgroundTask(_cleanup_temp_file, tmp_zip),
    )


@router.post("/{project_id}/upload")
def upload_project_zip(
    project_id: str,
    file: UploadFile = File(...),
    project_name: str = Form(..., min_length=1),
    current_user: str = Depends(require_auth),
):
    if current_user == "guest":
        raise HTTPException(status_code=403, detail="guest cannot upload project")

    project_name = project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="project_name cannot be empty")

    if not (file.filename or "").lower().endswith(".gsea"):
        raise HTTPException(status_code=400, detail="Only .gsea is supported")

    existing = None
    try:
        existing = get_project_record(project_id)
    except HTTPException as e:
        if e.status_code != 404:
            raise

    if existing and existing["user_id"] != current_user:
        raise HTTPException(status_code=403, detail="Project already owned by another user")

    target_user_id = current_user

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
                (target_user_id, project_name, ts, project_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO projects (project_id, user_id, project_name, create_time, access_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, target_user_id, project_name, ts, ts),
            )
        conn.commit()

    touch_access_time(project_id)
    return {"ok": True, "project_id": project_id, "user_id": target_user_id, "project_name": project_name}
