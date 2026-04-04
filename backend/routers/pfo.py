from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from backend.services.group_config import load_group_equities, load_project_config, save_group_equities, save_project_config
from backend.services.pfo import render_pfo_xml
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
    date_range_config: dict | None = None
    sharpe_config: dict | None = None


@router.get("")
def get_pfo(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    folder = project_dir(project_id)
    legacy_path = folder / "project.pfo"
    if legacy_path.exists():
        touch_access_time(project_id)
        return FileResponse(path=legacy_path, media_type="application/xml", filename="project.pfo")

    equities = load_group_equities(folder)
    if not equities:
        raise HTTPException(status_code=404, detail="PFO not found")
    cfg = load_project_config(folder)
    xml = render_pfo_xml(
        equities,
        commission_config=cfg.get("commission_config"),
        description=cfg.get("description", ""),
        date_range_config=cfg.get("date_range_config"),
        sharpe_config=cfg.get("sharpe_config"),
    )
    touch_access_time(project_id)
    return Response(content=xml, media_type="application/xml")


@router.put("")
def put_pfo(project_id: str, payload: PfoSaveRequest, current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    folder = project_dir(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    save_group_equities(folder, [item.model_dump() for item in payload.equities])
    save_project_config(
        folder,
        commission_config=payload.commission_config,
        description=payload.description,
        date_range_config=payload.date_range_config,
        sharpe_config=payload.sharpe_config,
    )
    (folder / "project.pfo").unlink(missing_ok=True)
    touch_access_time(project_id)
    return {"ok": True, "filename": "group.json"}
