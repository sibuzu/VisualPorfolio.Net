from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.services.auth import (
    ADMIN_PASSWORD,
    TOKEN_TTL_SECONDS,
    authenticate_user,
    clear_admin_cookie,
    clear_auth_cookies,
    create_user,
    issue_admin_token,
    issue_token,
    require_admin,
    require_auth,
    set_admin_cookie,
    set_auth_cookies,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class AdminLoginRequest(BaseModel):
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


@router.post("/admin/login")
def admin_login(payload: AdminLoginRequest, request: Request, response: Response):
    if payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    token = issue_admin_token()
    set_admin_cookie(response, request, token)
    return {"ok": True, "user": "admin", "expired_in": TOKEN_TTL_SECONDS}


@router.post("/admin/logout")
def admin_logout(request: Request, response: Response):
    clear_admin_cookie(response, request)
    return {"ok": True}


@router.get("/admin/me")
def admin_me(_: bool = Depends(require_admin)):
    return {"ok": True, "user": "admin"}
