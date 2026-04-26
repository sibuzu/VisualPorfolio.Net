from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.models.buy_hold import BuyHoldRequest, BuyHoldResponse
from backend.services.auth import require_auth
from backend.services.buy_hold import BuyHoldError, build_buy_hold_sea, save_buy_hold_sea
from backend.services.project_access import get_project_access, project_dir, touch_access_time


router = APIRouter(prefix="/projects/{project_id}/buy-hold", tags=["buy-hold"])


@router.post("", response_model=BuyHoldResponse)
def create_buy_hold(project_id: str, payload: BuyHoldRequest, current_user: str = Depends(require_auth)):
    _, access = get_project_access(project_id, current_user)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Read-only project")

    folder = project_dir(project_id)
    try:
        result = build_buy_hold_sea(
            folder=folder,
            buy_date=payload.date,
            amount_wan_text=payload.amount_wan,
            product_type=payload.product_type,
            code=payload.code,
            leverage_text=payload.leverage,
        )
        save_buy_hold_sea(folder, result)
    except BuyHoldError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    touch_access_time(project_id)
    return BuyHoldResponse(filename=result.filename, display_name=result.display_name)
