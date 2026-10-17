from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/auth", tags=["auth"])
AUTH_URL = os.getenv("VISUAL_PORTFOLIO_AUTH_URL", "http://127.0.0.1:8000").rstrip("/")
COOKIE_NAMES = ("user_id", "auth_token")


class AuthRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10)


async def _upstream(method: str, path: str, **kwargs) -> httpx.Response:
    try:
        async with _client() as client:
            cookies = kwargs.pop("cookies", None)
            if cookies:
                client.cookies.update(cookies)
            return await client.request(method, f"{AUTH_URL}{path}", **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Login service is unavailable") from exc


def _raise_upstream_error(result: httpx.Response) -> None:
    if result.status_code < 400:
        return
    if result.status_code in {400, 401, 403, 409, 422}:
        try:
            detail = result.json().get("detail", "Login failed")
        except (ValueError, AttributeError):
            detail = "Login failed"
        raise HTTPException(status_code=result.status_code, detail=detail)
    raise HTTPException(status_code=502, detail="Login service returned an error")


def _secure_cookie(request: Request) -> bool:
    return request.url.scheme == "https" or request.url.hostname not in {"localhost", "127.0.0.1", "testserver"}


def _cookie_values(request: Request) -> dict[str, str]:
    return {name: request.cookies.get(name, "") for name in COOKIE_NAMES}


async def require_user(request: Request) -> str:
    cookies = _cookie_values(request)
    if not all(cookies.values()) or cookies["user_id"] == "guest":
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await _upstream("GET", "/auth/me", cookies=cookies)
    if result.status_code != 200:
        if result.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        _raise_upstream_error(result)
        raise HTTPException(status_code=502, detail="Login service returned an error")
    try:
        user_id = result.json().get("user_id")
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=502, detail="Login service returned an invalid response") from exc
    if user_id != cookies["user_id"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return str(user_id)


@router.post("/signup")
async def signup(payload: AuthRequest) -> dict:
    result = await _upstream("POST", "/auth/signup", json=payload.model_dump())
    _raise_upstream_error(result)
    return {"ok": True}


@router.post("/login")
async def login(payload: AuthRequest, request: Request, response: Response) -> dict:
    result = await _upstream("POST", "/auth/login", json=payload.model_dump())
    _raise_upstream_error(result)
    try:
        body = result.json()
        user_id = body["user_id"]
        age = int(body["expired_in"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Login service returned an invalid response") from exc
    if user_id == "guest" or user_id != payload.user_id.strip() or age <= 0:
        raise HTTPException(status_code=502, detail="Login service returned an invalid response")
    cookies = {name: result.cookies.get(name) for name in COOKIE_NAMES}
    if cookies["user_id"] != user_id or not cookies["auth_token"]:
        raise HTTPException(status_code=502, detail="Login service did not issue a session")
    for name, value in cookies.items():
        response.set_cookie(name, value, max_age=age, httponly=True,
                            secure=_secure_cookie(request), samesite="lax", path="/")
    return {"ok": True, "user_id": user_id, "expired_in": age}


@router.get("/me")
async def me(user_id: str = Depends(require_user)) -> dict:
    return {"ok": True, "user_id": user_id}


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    for name in COOKIE_NAMES:
        response.delete_cookie(name, httponly=True, secure=_secure_cookie(request),
                               samesite="lax", path="/")
    return {"ok": True}
