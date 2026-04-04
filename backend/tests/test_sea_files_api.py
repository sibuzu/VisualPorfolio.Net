from __future__ import annotations

import io
import uuid
import zipfile

from fastapi.testclient import TestClient

from backend.main import app


def _new_user(prefix: str) -> tuple[str, str]:
    token = uuid.uuid4().hex[:8]
    return (f"{prefix}_{token}", f"pw_{token}")


def _signup_and_login(client: TestClient, user_id: str, password: str) -> None:
    signup = client.post("/auth/signup", json={"user_id": user_id, "password": password})
    assert signup.status_code == 200
    login = client.post("/auth/login", json={"user_id": user_id, "password": password})
    assert login.status_code == 200


def _create_project(client: TestClient, name: str) -> str:
    resp = client.post("/projects", json={"project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _make_sea_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("demo/strategy.toml", '[params."基本設定"]\n"滑價成本" = "0"\n')
        zf.writestr(
            "demo/events.jsonl",
            "\n".join(
                [
                    '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":100,"quantity":1}}',
                    '{"timestamp":"2025-01-02T00:00:00Z","type":"price","data":{"instrument_id":"SPY","price":101}}',
                    '{"timestamp":"2025-01-03T00:00:00Z","type":"trade","data":{"instrument_id":"SPY","price":102,"quantity":-1}}',
                ]
            ),
        )
    return buf.getvalue()


def test_upload_sea_and_run_analysis():
    with TestClient(app) as client:
        user, pw = _new_user("sea")
        _signup_and_login(client, user, pw)
        project_id = _create_project(client, "sea-analysis")

        payload = _make_sea_bytes()
        upload = client.post(
            f"/projects/{project_id}/files",
            files={"file": ("demo.sea", payload, "application/zip")},
        )
        assert upload.status_code == 200

        run = client.post(
            f"/projects/{project_id}/analysis",
            json={
                "equities": [
                    {
                        "filename": "demo.sea",
                        "active": True,
                        "contract": 1,
                        "weight": 1,
                        "color": "#0a9396",
                        "name": "demo",
                    }
                ],
                "date_range": {"all": True},
                "options": {"risk_free_rate": 0, "mdd_count": 5, "commission_per_trade": 0},
            },
        )
        assert run.status_code == 200
        assert run.json()["summary"]["trade_count"] > 0
