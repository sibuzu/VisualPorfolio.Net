from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import strategy_report.auth as auth
from strategy_report.main import app


SAMPLE = Path(__file__).parent / "fixtures" / "BDS_TXF.srp"


@pytest.fixture
def fake_visual_portfolio_auth(monkeypatch):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            return httpx.Response(200, json={"ok": True, "user_id": "demo", "expired_in": 3600}, headers=[
                ("set-cookie", "user_id=demo; Path=/; HttpOnly"),
                ("set-cookie", "auth_token=signed-demo; Path=/; HttpOnly"),
            ])
        if request.url.path == "/auth/me":
            if "auth_token=signed-demo" in request.headers.get("cookie", ""):
                return httpx.Response(200, json={"ok": True, "user_id": "demo"})
            return httpx.Response(401, json={"detail": "Unauthorized"})
        if request.url.path == "/auth/signup":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)

    monkeypatch.setattr(auth, "_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handle)))


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"user_id": "demo", "password": "example"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "demo"


def test_health_and_report_api(fake_visual_portfolio_auth):
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        payload = SAMPLE.read_bytes()
        assert client.post("/api/report", files={"file": ("report.srp", payload)}).status_code == 401
        _login(client)
        assert client.get("/api/auth/me").json()["user_id"] == "demo"
        response = client.post("/api/report", files={"file": ("report.srp", payload)},
                               data={"settings": '{"mode":"backtest"}'})
        assert response.status_code == 200
        report = response.json()
        assert report["source"]["format"] == "srp"
        assert report["compound"]["summary"]["trade_count"] > 0
        assert report["compound"]["periods"]["annual"]
        assert client.post("/api/report", files={"file": ("bad.txt", b"bad")}).status_code == 422
        assert client.post("/api/auth/logout").status_code == 200
        assert client.get("/api/auth/me").status_code == 401


def test_signup_uses_visual_portfolio_account_service(fake_visual_portfolio_auth):
    with TestClient(app) as client:
        response = client.post("/api/auth/signup", json={"user_id": "demo", "password": "example"})
        assert response.status_code == 200


def test_authentication_precedes_multipart_parsing(fake_visual_portfolio_auth):
    with TestClient(app) as client:
        response = client.post("/api/report", content=b"not multipart",
                               headers={"content-type": "multipart/form-data; boundary=missing"})
        assert response.status_code == 401


def test_public_hostname_sets_secure_host_only_cookies(fake_visual_portfolio_auth):
    with TestClient(app, base_url="http://strategyreport.sibuzu.com") as client:
        response = client.post("/api/auth/login", json={"user_id": "demo", "password": "example"})
        assert response.status_code == 200
        cookies = response.headers.get_list("set-cookie")
        assert len(cookies) == 2
        assert all("Secure" in cookie and "HttpOnly" in cookie and "domain=" not in cookie.lower()
                   for cookie in cookies)


def test_concurrent_requests_are_independent(fake_visual_portfolio_auth):
    def one(capital: int) -> float:
        body = (
            '<策略回測><參數><策略>Demo</策略></參數><策略交易>'
            '<Trade time_stamp="2024/01/01 09:00:00" bs="B" contract="1" price="100"/>'
            '<Trade time_stamp="2024/01/02 09:00:00" bs="S" contract="1" price="105"/>'
            '</策略交易></策略回測>'
        ).encode()
        with TestClient(app) as client:
            _login(client)
            response = client.post("/api/report", files={"file": ("demo.srp", body)},
                                   data={"settings": f'{{"mode":"fixed_quantity","initial_capital":{capital}}}'})
            assert response.status_code == 200
            return response.json()["compound"]["summary"]["final_capital"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, (100_000, 200_000)))
    assert results == [100_005, 200_005]
