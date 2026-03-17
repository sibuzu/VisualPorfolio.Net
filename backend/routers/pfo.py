from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.services.pfo import save_pfo
from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.auth import require_auth

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
    commission_config: dict[str, float] | None = None
    description: str | None = None


@router.get("")
def get_pfo(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    path = project_dir(project_id) / "project.pfo"
    if not path.exists():
        raise HTTPException(status_code=404, detail="PFO not found")
    touch_access_time(project_id)
    return FileResponse(path=path, media_type="application/xml", filename="project.pfo")


@router.put("")
def put_pfo(project_id: str, payload: PfoSaveRequest, current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    path = project_dir(project_id) / "project.pfo"
    save_pfo(
        path,
        [item.model_dump() for item in payload.equities],
        commission_config=payload.commission_config,
        description=payload.description,
    )
    touch_access_time(project_id)
    return {"ok": True, "filename": path.name}
