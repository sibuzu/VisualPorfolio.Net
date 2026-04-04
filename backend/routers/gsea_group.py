from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.services.group_config import save_group_equities, save_project_config
from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.auth import require_auth

router = APIRouter(prefix="/projects/{project_id}/gsea-group", tags=["gsea-group"])


class GseaGroupItem(BaseModel):
    index: int
    filename: str
    color: str = "Blue"
    weight: float = 1.0
    contract: float = 1.0
    active: bool = True
    name: str = ""


class GseaGroupSaveRequest(BaseModel):
    equities: list[GseaGroupItem] = Field(default_factory=list)
    commission_config: dict[str, float] | None = None
    description: str | None = None
    date_range_config: dict | None = None
    sharpe_config: dict | None = None


@router.get("")
def get_gsea_group(project_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    folder = project_dir(project_id)
    group_path = folder / "group.json"
    if not group_path.exists():
        raise HTTPException(status_code=404, detail="group.json not found")
    touch_access_time(project_id)
    return Response(content=group_path.read_text(encoding="utf-8-sig"), media_type="application/json")


@router.put("")
def put_gsea_group(project_id: str, payload: GseaGroupSaveRequest, current_user: str = Depends(require_auth)):
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
    touch_access_time(project_id)
    return {"ok": True, "filename": "group.json"}
