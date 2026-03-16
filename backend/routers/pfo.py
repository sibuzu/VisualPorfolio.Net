from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.services.pfo import save_pfo
from backend.services.project_access import get_project_access, project_dir, touch_access_time

router = APIRouter(prefix="/projects/{project_id}/pfo", tags=["pfo"])


class PfoItem(BaseModel):
    index: int
    filename: str
    color: str = "Blue"
    weight: float = 1.0
    contract: float = 1.0
    active: bool = True
    name: str = ""


class PfoSaveRequest(BaseModel):
    equities: list[PfoItem] = Field(default_factory=list)


@router.get("")
def get_pfo(project_id: str, guest_id: str = Query(..., min_length=8)):
    get_project_access(project_id, guest_id)
    path = project_dir(project_id) / "project.pfo"
    if not path.exists():
        raise HTTPException(status_code=404, detail="PFO not found")
    touch_access_time(project_id)
    return FileResponse(path=path, media_type="application/xml", filename="project.pfo")


@router.put("")
def put_pfo(project_id: str, payload: PfoSaveRequest, guest_id: str = Query(..., min_length=8)):
    _, access = get_project_access(project_id, guest_id)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    path = project_dir(project_id) / "project.pfo"
    save_pfo(path, [item.model_dump() for item in payload.equities])
    touch_access_time(project_id)
    return {"ok": True, "filename": path.name}
