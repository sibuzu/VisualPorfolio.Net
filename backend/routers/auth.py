from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.services.auth import (
    TOKEN_TTL_SECONDS,
    authenticate_user,
    clear_auth_cookies,
    create_user,
    issue_token,
    require_auth,
    set_auth_cookies,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


@router.post("/signup")
def signup(payload: AuthRequest):
    create_user(payload.user_id.strip(), payload.password)
    return {"ok": True}


@router.post("/login")
def login(payload: AuthRequest, request: Request, response: Response):
    user_id = payload.user_id.strip()
    if not authenticate_user(user_id, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_token(user_id)
    set_auth_cookies(response, request, user_id, token)
    return {"ok": True, "user_id": user_id, "expired_in": TOKEN_TTL_SECONDS}


@router.post("/logout")
def logout(request: Request, response: Response):
    clear_auth_cookies(response, request)
    return {"ok": True}


@router.get("/me")
def me(current_user: str = Depends(require_auth)):
    return {"ok": True, "user_id": current_user}
