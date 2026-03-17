from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.auth import require_auth

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])

_ALLOWED = {".srp", ".xrp"}
_ATTACHMENT_ALLOWED = {".png", ".jpg", ".jpeg"}
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _validate_filename(name: str) -> None:
    ext = Path(name).suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Only .srp/.xrp are allowed")


def _sanitize_filename(name: str, allowed_ext: set[str]) -> str:
    base = Path(name or "").name
    stem = Path(base).stem
    ext = Path(base).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg are allowed")
    stem = _SAFE_NAME_RE.sub("_", stem).strip("._") or "image"
    return f"{stem}{ext}"


def _attachments_dir(project_id: str) -> Path:
    folder = project_dir(project_id) / "attachments"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _utc_ts_prefix() -> str:
    # Lexicographically sortable timestamp prefix (earlier upload => smaller filename).
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")[:-3]


@router.get("")
def list_files(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    folder = project_dir(project_id)
    folder.mkdir(parents=True, exist_ok=True)

    items = []
    for p in sorted(folder.iterdir()):
        if p.is_file():
            items.append({"filename": p.name, "size": p.stat().st_size})

    touch_access_time(project_id)
    return {"files": items}


@router.post("")
async def upload_file(project_id: str, file: UploadFile = File(...), current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    _validate_filename(file.filename)
    payload = await file.read()

    try:
        ET.fromstring(payload.decode("utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {exc}") from exc

    folder = project_dir(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    out_path = folder / file.filename
    out_path.write_bytes(payload)

    touch_access_time(project_id)
    return {"ok": True, "filename": file.filename}


@router.delete("/{filename}")
def delete_file(project_id: str, filename: str, current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    path = project_dir(project_id) / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    path.unlink()
    touch_access_time(project_id)
    return {"deleted": True, "filename": filename}


@router.get("/attachments")
def list_attachments(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    folder = _attachments_dir(project_id)
    items = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in _ATTACHMENT_ALLOWED:
            items.append({"filename": p.name, "size": p.stat().st_size})
    touch_access_time(project_id)
    return {"attachments": items}


@router.post("/attachments")
async def upload_attachment(project_id: str, file: UploadFile = File(...), current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    safe_name = _sanitize_filename(file.filename or "image.png", _ATTACHMENT_ALLOWED)
    stem = Path(safe_name).stem
    ext = Path(safe_name).suffix.lower()
    safe_name = f"{_utc_ts_prefix()}_{stem}{ext}"
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")

    folder = _attachments_dir(project_id)
    out_path = folder / safe_name
    base_stem = Path(safe_name).stem
    seq = 1
    while out_path.exists():
        out_path = folder / f"{base_stem}_{seq}{ext}"
        seq += 1

    out_path.write_bytes(payload)
    touch_access_time(project_id)
    return {"ok": True, "filename": out_path.name}


@router.get("/attachments/{filename}")
def get_attachment(project_id: str, filename: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    safe_name = _sanitize_filename(filename, _ATTACHMENT_ALLOWED)
    path = _attachments_dir(project_id) / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment not found")
    touch_access_time(project_id)
    media = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(path=path, media_type=media, filename=path.name)


@router.delete("/attachments/{filename}")
def delete_attachment(project_id: str, filename: str, current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    safe_name = _sanitize_filename(filename, _ATTACHMENT_ALLOWED)
    path = _attachments_dir(project_id) / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment not found")

    path.unlink()
    touch_access_time(project_id)
    return {"deleted": True, "filename": safe_name}
