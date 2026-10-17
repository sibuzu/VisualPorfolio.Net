from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from zipfile import ZipFile

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import strategy_report.auth as auth
import strategy_report.storage as storage
from strategy_report.analysis import CalculationSettings
from strategy_report.importer import parse_report
from strategy_report.main import app


SAMPLE = Path(__file__).parent / "fixtures" / "BDS_TXF.srp"
SEA_SAMPLE = Path(__file__).parent / "fixtures" / "BDS_TXF.sea"


@pytest.fixture
def fake_visual_portfolio_auth(monkeypatch):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            payload = json.loads(request.content)
            user_id = payload["user_id"]
            if user_id not in {"demo", "other"} or payload["password"] != "example":
                return httpx.Response(401, json={"detail": "Invalid credentials"})
            return httpx.Response(200, json={"ok": True, "user_id": user_id, "expired_in": 3600}, headers=[
                ("set-cookie", f"user_id={user_id}; Path=/; HttpOnly"),
                ("set-cookie", f"auth_token=signed-{user_id}; Path=/; HttpOnly"),
            ])
        if request.url.path == "/auth/me":
            cookies = request.headers.get("cookie", "")
            for user_id in ("demo", "other"):
                if f"auth_token=signed-{user_id}" in cookies:
                    return httpx.Response(200, json={"ok": True, "user_id": user_id})
            return httpx.Response(401, json={"detail": "Unauthorized"})
        if request.url.path == "/auth/signup":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)

    monkeypatch.setattr(auth, "_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handle)))


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"user_id": "demo", "password": "example"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "demo"


def test_backtest_capital_override_is_saved_and_can_be_reset(fake_visual_portfolio_auth):
    with TestClient(app) as client:
        _login(client)
        created = client.post("/api/performances", files={"file": (SAMPLE.name, SAMPLE.read_bytes())})
        item_id = created.json()["performance"]["performance_id"]
        endpoint = f"/api/performances/{item_id}/report"
        automatic = client.post(endpoint, json={"mode": "backtest"})
        assert automatic.status_code == 200
        assert automatic.json()["compound"]["summary"]["initial_capital"] == 100_000

        manual = client.post(endpoint, json={"mode": "backtest", "backtest_initial_capital": 150_000})
        assert manual.status_code == 200
        assert manual.json()["compound"]["summary"]["initial_capital"] == 150_000
        assert manual.json()["compound"]["summary"]["net_profit"] == automatic.json()["compound"]["summary"]["net_profit"]
        assert client.get(f"/api/performances/{item_id}").json()["performance"]["settings"]["backtest_initial_capital"] == "150000"

        restored = client.post(endpoint, json={"mode": "backtest", "backtest_initial_capital": None})
        assert restored.status_code == 200
        assert restored.json()["compound"]["summary"]["initial_capital"] == 100_000
        assert client.get(f"/api/performances/{item_id}").json()["performance"]["settings"]["backtest_initial_capital"] is None


def test_date_range_defaults_owner_memory_and_viewer_isolation(fake_visual_portfolio_auth, tmp_path):
    body = ('<策略回測><參數><策略>Dates</策略><開始日期>2012/01/01</開始日期>'
            '<結束日期>2026/12/31</結束日期></參數><策略交易>'
            '<Trade time_stamp="2012/01/18 09:00:00" bs="B" contract="1" price="100"/>'
            '<Trade time_stamp="2026/08/11 09:00:00" bs="S" contract="1" price="105"/>'
            '</策略交易></策略回測>').encode()
    with TestClient(app) as client:
        _login(client)
        item_id = client.post("/api/performances", files={"file": ("dates.srp", body)}).json()["performance"]["performance_id"]
        url = f"/api/performances/{item_id}"
        item = client.get(url).json()["performance"]
        assert item["source_range"] == {"start": "2012-01-18", "end": "2026-08-11"}
        assert item["settings"]["date_start"] is None
        settings = {"date_start": "2026-01-01", "date_end": "2026-08-11", "date_range_enabled": True}
        selected = client.post(url + "/report", json=settings)
        assert selected.status_code == 200
        # The only in-range event closes a position opened before the range.
        assert selected.json()["simple"]["summary"]["trade_count"] == 0
        assert selected.json()["source"]["date_range"] == item["source_range"]
        settings["date_range_enabled"] = False
        full = client.post(url + "/report", json=settings)
        assert full.json()["simple"]["summary"]["trade_count"] == 2
        path = tmp_path / "reports" / item_id / "config.json"
        saved = path.read_bytes()
        reopened = client.get(url).json()["performance"]["settings"]
        assert all(reopened[key] == value for key, value in settings.items())
        client.post("/api/auth/login", json={"user_id": "other", "password": "example"})
        assert client.post(url + "/report", json={**settings, "date_start": "2015-01-01", "date_range_enabled": True}).status_code == 200
        assert path.read_bytes() == saved
        assert client.get(url).json()["performance"]["settings"] == reopened


def test_buy_hold_owner_persistence_copy_and_viewer_isolation(fake_visual_portfolio_auth, monkeypatch, tmp_path):
    import strategy_report.buy_hold as bh
    monkeypatch.setattr(bh, "_market_data", lambda *args: ([
        {"date": "2024-01-02", "close": 100}, {"date": "2024-01-05", "close": 110}], []))
    body = ('<策略回測><參數><策略>Demo</策略></參數><策略交易>'
            '<Trade time_stamp="2024/01/02 09:00:00" bs="B" contract="1" price="100"/>'
            '<Trade time_stamp="2024/01/05 09:00:00" bs="S" contract="1" price="105"/>'
            '</策略交易></策略回測>').encode()
    with TestClient(app) as client:
        _login(client)
        item = client.post("/api/performances", files={"file": ("demo.srp", body)}).json()["performance"]
        item_id = item["performance_id"]
        path = tmp_path / "reports" / item_id / "config.json"
        response = client.post(f"/api/performances/{item_id}/report", json={"buy_hold": {"amount_wan": 100}})
        assert response.status_code == 200
        assert response.json()["buy_hold"]["final_capital"] == 1100000
        assert [row["side"] for row in response.json()["buy_hold"]["detail"]] == ["B", "S"]
        saved = path.read_bytes()
        assert json.loads(saved)["buy_hold"]["amount_wan"] == "100"
        copy = client.post(f"/api/performances/{item_id}/copy", json={}).json()["performance"]
        assert copy["performance_id"] != item_id
        assert copy["settings"]["buy_hold"] == json.loads(saved)["buy_hold"]
        client.post("/api/auth/login", json={"user_id": "other", "password": "example"})
        response = client.post(f"/api/performances/{item_id}/report", json={"buy_hold": {"amount_wan": 200}})
        assert response.status_code == 200
        assert response.json()["buy_hold"]["final_capital"] == 2200000
        assert path.read_bytes() == saved
        response = client.post(f"/api/performances/{item_id}/report", json={"buy_hold": None})
        assert response.json()["buy_hold"] is None
        assert path.read_bytes() == saved
        _login(client)
        client.post(f"/api/performances/{item_id}/report", json={"buy_hold": None})
        assert json.loads(path.read_bytes())["buy_hold"] is None
        assert (path.parent / "source.srp").read_bytes() == body


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


def test_saved_performance_management_and_user_isolation(fake_visual_portfolio_auth, monkeypatch, tmp_path):
    monkeypatch.setenv("STRATEGY_REPORT_DATA_DIR", str(tmp_path))
    payload = SAMPLE.read_bytes()
    expected_name = parse_report(SAMPLE.name, payload).strategy
    with TestClient(app) as client:
        assert client.get("/api/performances").status_code == 401
        _login(client)
        created = client.post("/api/performances", files={"file": (SAMPLE.name, payload)})
        assert created.status_code == 201
        item = created.json()["performance"]
        item_id = item["performance_id"]
        assert item_id == storage.performance_id(payload)
        assert len(item_id) == 9 and item_id.startswith("SR-") and item_id[3:].isalpha()
        assert item["name"] == expected_name
        assert created.json()["created"] is True
        assert (tmp_path / "reports" / item_id / "source.srp").read_bytes() == payload
        config_path = tmp_path / "reports" / item_id / "config.json"
        assert json.loads(config_path.read_text()) == item["settings"]

        duplicate = client.post("/api/performances", files={"file": ("renamed.srp", payload)}, data={"name": "Different"})
        assert duplicate.status_code == 200
        assert duplicate.json()["created"] is False
        assert duplicate.json()["performance"]["performance_id"] == item_id
        assert duplicate.json()["performance"]["name"] == expected_name

        changed = client.patch(f"/api/performances/{item_id}", json={"name": "我的策略", "important": True})
        assert changed.json()["performance"]["name"] == "我的策略"
        assert changed.json()["performance"]["important"] is True
        report = client.post(f"/api/performances/{item_id}/report", json={"mode": "fixed_quantity", "initial_capital": 120000})
        assert report.status_code == 200
        assert report.json()["compound"]["summary"]["initial_capital"] == 120000
        listed = client.get("/api/performances").json()["performances"]
        assert len(listed) == 1
        assert listed[0]["settings"]["initial_capital"] == "120000"
        assert listed[0]["important"] is True
        saved_config = config_path.read_bytes()
        assert json.loads(saved_config)["initial_capital"] == "120000"

        copied = client.post(f"/api/performances/{item_id}/copy", json={"name": "我的副本"})
        assert copied.status_code == 201
        copy = copied.json()["performance"]
        copy_id = copy["performance_id"]
        assert copy_id != item_id and copy_id.startswith("SR-")
        assert copy["is_owner"] is True and copy["name"] == "我的副本"
        assert copy["settings"]["initial_capital"] == "120000"
        assert (tmp_path / "reports" / copy_id / "source.srp").read_bytes() == payload
        downloaded = client.get(f"/api/performances/{copy_id}/download")
        assert downloaded.status_code == 200
        with ZipFile(BytesIO(downloaded.content)) as archive:
            assert archive.read("source.srp") == payload
            assert json.loads(archive.read("performance.json"))["performance_id"] == copy_id

    with TestClient(app) as client:
        _login(client)
        assert client.get(f"/api/performances/{item_id}").json()["performance"]["name"] == "我的策略"

    with TestClient(app) as other_client:
        login = other_client.post("/api/auth/login", json={"user_id": "other", "password": "example"})
        assert login.status_code == 200
        assert other_client.get("/api/performances").json()["performances"] == []
        important = other_client.get("/api/performances/important").json()["performances"]
        assert [item["performance_id"] for item in important] == [item_id]
        shared = other_client.get(f"/api/performances/{item_id}")
        assert shared.status_code == 200 and shared.json()["performance"]["is_owner"] is False
        temporary = other_client.post(f"/api/performances/{item_id}/report", json={"initial_capital": 250000})
        assert temporary.status_code == 200
        assert temporary.json()["compound"]["summary"]["initial_capital"] == 250000
        assert other_client.get(f"/api/performances/{item_id}").json()["performance"]["settings"]["initial_capital"] == "120000"
        assert config_path.read_bytes() == saved_config
        assert other_client.patch(f"/api/performances/{item_id}", json={"name": "No"}).status_code == 403
        assert other_client.delete(f"/api/performances/{item_id}").status_code == 403
        own_copy = other_client.post(f"/api/performances/{item_id}/copy", json={})
        assert own_copy.status_code == 201
        assert own_copy.json()["performance"]["owner_id"] == "other"
        assert own_copy.json()["performance"]["performance_id"] not in {item_id, copy_id}

    with TestClient(app) as client:
        _login(client)
        assert client.delete(f"/api/performances/{item_id}").status_code == 200
        assert not (tmp_path / "reports" / item_id).exists()
        assert len(client.get("/api/performances").json()["performances"]) == 1


def test_short_id_collision_never_replaces_existing_file(monkeypatch, tmp_path):
    monkeypatch.setenv("STRATEGY_REPORT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(storage, "performance_id", lambda _content: "SR-AAAAAA")
    first = (
        '<策略回測><參數><策略>First</策略></參數><策略交易>'
        '<Trade time_stamp="2024/01/01 09:00:00" bs="B" contract="1" price="100"/>'
        '</策略交易></策略回測>'
    ).encode()
    second = first.replace(b"First", b"Second")
    original, created = storage.create_performance("demo", first, parse_report("first.srp", first), "")
    assert created is True
    with pytest.raises(HTTPException) as error:
        storage.create_performance("demo", second, parse_report("second.srp", second), "")
    assert error.value.status_code == 409
    saved, content = storage.get_performance("demo", original["performance_id"], include_content=True)
    assert saved["name"] == "First"
    assert content == first


def test_saved_sea_can_be_reopened_and_analyzed(fake_visual_portfolio_auth, monkeypatch, tmp_path):
    monkeypatch.setenv("STRATEGY_REPORT_DATA_DIR", str(tmp_path))
    with TestClient(app) as client:
        _login(client)
        created = client.post("/api/performances", files={"file": (SEA_SAMPLE.name, SEA_SAMPLE.read_bytes())})
        assert created.status_code == 201
        item = created.json()["performance"]
        assert item["source_format"] == "sea"
        result = client.post(f'/api/performances/{item["performance_id"]}/report', json={"mode": "backtest"})
        assert result.status_code == 200
        assert result.json()["source"]["format"] == "sea"


def test_legacy_blob_reports_migrate_to_report_directories(monkeypatch, tmp_path):
    monkeypatch.setenv("STRATEGY_REPORT_DATA_DIR", str(tmp_path))
    payload = SAMPLE.read_bytes()
    item_id = storage.performance_id(payload)
    with sqlite3.connect(tmp_path / "performances.db") as connection:
        connection.execute("""
            CREATE TABLE performances (user_id TEXT NOT NULL, performance_id TEXT NOT NULL,
                file_hash TEXT NOT NULL, name TEXT NOT NULL, strategy_name TEXT NOT NULL,
                filename TEXT NOT NULL, source_format TEXT NOT NULL, content BLOB NOT NULL,
                settings_json TEXT NOT NULL, important INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, accessed_at TEXT NOT NULL,
                PRIMARY KEY (user_id, performance_id))
        """)
        connection.execute("""
            INSERT INTO performances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("demo", item_id, "legacy-hash", "原有績效", "Strategy", SAMPLE.name, "srp", payload,
              CalculationSettings().model_dump_json(), 1, "2026-10-14", "2026-10-14"))
    item, restored = storage.get_performance("demo", item_id, include_content=True)
    assert item["name"] == "原有績效" and restored == payload
    assert (tmp_path / "reports" / item_id / "source.srp").read_bytes() == payload
    with sqlite3.connect(tmp_path / "db" / "reporsts.db") as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(performances)")}
    assert "content" not in columns and "owner_id" in columns
    assert "settings_json" not in columns
    assert json.loads((tmp_path / "reports" / item_id / "config.json").read_text()) == item["settings"]
