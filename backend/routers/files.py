from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.auth import require_auth

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])

_ALLOWED = {".srp", ".xrp"}


def _validate_filename(name: str) -> None:
    ext = Path(name).suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Only .srp/.xrp are allowed")


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
