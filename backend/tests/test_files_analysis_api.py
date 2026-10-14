import io
import json
from pathlib import Path
import uuid
import zipfile

from fastapi.testclient import TestClient

from backend.main import app


def _new_user(prefix: str) -> tuple[str, str]:
    token = uuid.uuid4().hex[:8]
    return f"{prefix}_{token}", f"pw_{token}"


def _signup_and_login(client: TestClient, user_id: str, password: str) -> None:
    assert client.post("/auth/signup", json={"user_id": user_id, "password": password}).status_code == 200
    assert client.post("/auth/login", json={"user_id": user_id, "password": password}).status_code == 200


def _create_project(client: TestClient, user_id: str, project_name: str = "test-project") -> str:
    resp = client.post(
        "/projects",
        json={"user_id": user_id, "project_name": project_name},
    )
    assert resp.status_code == 200
    return resp.json()["project_id"]


def test_upload_and_analysis_flow():
    sample = Path("ref_result/project/aa-1.srp")
    payload = sample.read_bytes()

    with TestClient(app) as client:
        owner, password = _new_user("analysis_owner")
        _signup_and_login(client, owner, password)
        project_id = _create_project(client, owner, "analysis-project")

        up = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": owner},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert up.status_code == 200

        listing = client.get(f"/projects/{project_id}/files", params={"user_id": owner})
        assert listing.status_code == 200
        assert any(x["filename"] == "aa-1.sea" for x in listing.json()["files"])

        run = client.post(
            f"/projects/{project_id}/analysis",
            params={"user_id": owner},
            json={
                "equities": [
                    {
                        "filename": "aa-1.sea",
                        "active": True,
                        "contract": 1,
                        "weight": 1,
                        "color": "#0a9396",
                        "name": "aa-1",
                    }
                ],
                "date_range": {"all": True},
                "options": {"risk_free_rate": 0, "mdd_count": 5, "commission_per_trade": 0},
            },
        )
        assert run.status_code == 200
        body = run.json()
        assert "summary" in body
        assert "equity_curve" in body
        assert "monthly" in body
        assert "annual" in body
        assert "weekly" in body
        assert "position_analysis" in body
        assert "win_loss" in body
        assert "commission" in body
        assert "diversity" in body
        assert "mdd_markers" in body
        assert "dynamic_compounding" in body
        assert "weekly" in body["dynamic_compounding"]
        assert "monthly" in body["dynamic_compounding"]
        for key in (
            "initial_net_value",
            "final_net_value",
            "profit_multiple",
            "cagr_pct",
            "mdd_pct",
            "mdd_amount",
            "mdd_pct_date",
            "mdd_amount_date",
            "reach_10x_date",
        ):
            assert key in body["dynamic_compounding"]["weekly"]
            assert key in body["dynamic_compounding"]["monthly"]
        assert body["summary"]["trade_count"] > 0

        report = client.post(
            f"/projects/{project_id}/analysis/dynamic-compounding/weekly/download",
            params={"user_id": owner},
            json={
                "equities": [
                    {
                        "filename": "aa-1.sea",
                        "active": True,
                        "contract": 1,
                        "weight": 1,
                        "color": "#0a9396",
                        "name": "aa-1",
                    }
                ],
                "date_range": {"all": True},
                "options": {
                    "risk_free_rate": 0,
                    "mdd_count": 5,
                    "dynamic_compounding": {
                        "initial_capital": 80_000_000,
                        "initial_ratio": 0.1,
                        "add_threshold_profit": 100_000_000,
                        "add_ratio": 0.15,
                        "rollback_amount": 20_000_000,
                        "max_multiple": 10,
                    },
                },
            },
        )
        assert report.status_code == 200
        assert "每週調整" in report.headers["content-disposition"] or "%E6%AF%8F%E9%80%B1%E8%AA%BF%E6%95%B4" in report.headers["content-disposition"]
        with zipfile.ZipFile(io.BytesIO(report.content)) as archive:
            names = archive.namelist()
            event_name = next(name for name in names if name.endswith("/events.jsonl"))
            events = [json.loads(line) for line in archive.read(event_name).decode().splitlines()]
        assert len(events) > 0
        fund_events = [event for event in events if event["type"] == "fund"]
        trade_events = [event for event in events if event["type"] == "trade"]
        assert fund_events[0]["data"] == {"currency": "USD", "amount": 80_000_000.0}
        assert all("quantity" in event["data"] for event in trade_events)


def test_owner_edit_other_view_only_access_rules():
    sample = Path("ref_result/project/aa-1.srp")
    payload = sample.read_bytes()

    with TestClient(app) as client:
        owner, owner_password = _new_user("access_owner")
        stranger, stranger_password = _new_user("access_stranger")
        _signup_and_login(client, owner, owner_password)
        project_id = _create_project(client, owner, "access-project")
        up = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": owner},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert up.status_code == 200

        _signup_and_login(client, stranger, stranger_password)
        allowed = client.get(f"/projects/{project_id}", params={"user_id": stranger})
        assert allowed.status_code == 200

        stranger_list = client.get("/projects", params={"user_id": stranger})
        assert stranger_list.status_code == 200
        assert all(x["project_id"] != project_id for x in stranger_list.json()["projects"])

        readonly_upload = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": stranger},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert readonly_upload.status_code == 403
