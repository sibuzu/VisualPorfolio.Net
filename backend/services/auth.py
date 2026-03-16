from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Response

from backend.db.database import DB_DIR

USERS_DB_PATH = DB_DIR / "users.db"
TOKEN_TTL_SECONDS = 6 * 60 * 60
USER_COOKIE = "user_id"
TOKEN_COOKIE = "auth_token"
ADMIN_COOKIE = "admin_token"
SECRET = os.getenv("AUTH_TOKEN_SECRET", "visualportfolio-dev-secret")
ADMIN_PASSWORD = "jack6819"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(payload_b64: str) -> str:
    sig = hmac.new(SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url(sig)


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(_hash_password(password, salt), f"{salt}${digest}")


def _users_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_users_db() -> None:
    with _users_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                access_time TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_user(user_id: str, password: str) -> None:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if user_id.strip().lower() == "admin":
        raise HTTPException(status_code=400, detail="user_id 'admin' is reserved")
    if not password:
        raise HTTPException(status_code=400, detail="password is required")
    with _users_conn() as conn:
        row = conn.execute("SELECT user FROM users WHERE user = ?", (user_id,)).fetchone()
        if row:
            raise HTTPException(status_code=409, detail="user_id already exists")
        conn.execute(
            "INSERT INTO users (user, password, access_time) VALUES (?, ?, ?)",
            (user_id, _hash_password(password), _now_iso()),
        )
        conn.commit()


def authenticate_user(user_id: str, password: str) -> bool:
    with _users_conn() as conn:
        row = conn.execute("SELECT password FROM users WHERE user = ?", (user_id,)).fetchone()
    if not row:
        return False
    return _verify_password(password, row["password"])


def issue_token(user_id: str) -> str:
    exp = int(datetime.now(timezone.utc).timestamp()) + TOKEN_TTL_SECONDS
    payload = {"user_id": user_id, "exp": exp}
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    token = f"{payload_b64}.{_sign(payload_b64)}"
    with _users_conn() as conn:
        conn.execute("UPDATE users SET access_time = ? WHERE user = ?", (_now_iso(), user_id))
        conn.commit()
    return token


def verify_token(token: str) -> dict | None:
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(payload_b64), sig):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None
    exp = int(payload.get("exp", 0))
    if int(datetime.now(timezone.utc).timestamp()) >= exp:
        return None
    return payload


def issue_admin_token() -> str:
    exp = int(datetime.now(timezone.utc).timestamp()) + TOKEN_TTL_SECONDS
    payload = {"admin": True, "exp": exp}
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64)}"


def set_auth_cookies(response: Response, request: Request, user_id: str, token: str) -> None:
    secure = request.url.scheme == "https"
    same_site = "none" if secure else "lax"
    response.set_cookie(USER_COOKIE, user_id, max_age=TOKEN_TTL_SECONDS, httponly=True, secure=secure, samesite=same_site)
    response.set_cookie(TOKEN_COOKIE, token, max_age=TOKEN_TTL_SECONDS, httponly=True, secure=secure, samesite=same_site)


def clear_auth_cookies(response: Response, request: Request) -> None:
    secure = request.url.scheme == "https"
    same_site = "none" if secure else "lax"
    response.delete_cookie(USER_COOKIE, httponly=True, secure=secure, samesite=same_site)
    response.delete_cookie(TOKEN_COOKIE, httponly=True, secure=secure, samesite=same_site)


def set_admin_cookie(response: Response, request: Request, token: str) -> None:
    secure = request.url.scheme == "https"
    same_site = "none" if secure else "lax"
    response.set_cookie(ADMIN_COOKIE, token, max_age=TOKEN_TTL_SECONDS, httponly=True, secure=secure, samesite=same_site)


def clear_admin_cookie(response: Response, request: Request) -> None:
    secure = request.url.scheme == "https"
    same_site = "none" if secure else "lax"
    response.delete_cookie(ADMIN_COOKIE, httponly=True, secure=secure, samesite=same_site)


def require_auth(request: Request) -> str:
    user_id = request.cookies.get(USER_COOKIE, "")
    token = request.cookies.get(TOKEN_COOKIE, "")
    if not user_id or not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = verify_token(token)
    if not payload or payload.get("user_id") != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return str(user_id)


def require_admin(request: Request) -> bool:
    token = request.cookies.get(ADMIN_COOKIE, "")
    if not token:
        raise HTTPException(status_code=401, detail="Admin unauthorized")
    payload = verify_token(token)
    if not payload or payload.get("admin") is not True:
        raise HTTPException(status_code=401, detail="Admin unauthorized")
    return True
