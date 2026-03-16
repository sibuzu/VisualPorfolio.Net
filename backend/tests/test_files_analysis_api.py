from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


OWNER = "550e8400-e29b-41d4-a716-446655440001"
STRANGER = "550e8400-e29b-41d4-a716-446655440099"


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
        project_id = _create_project(client, OWNER, "analysis-project")

        up = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": OWNER},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert up.status_code == 200

        listing = client.get(f"/projects/{project_id}/files", params={"user_id": OWNER})
        assert listing.status_code == 200
        assert any(x["filename"] == "aa-1.srp" for x in listing.json()["files"])

        run = client.post(
            f"/projects/{project_id}/analysis",
            params={"user_id": OWNER},
            json={
                "equities": [
                    {
                        "filename": "aa-1.srp",
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
        assert body["summary"]["trade_count"] > 0


def test_owner_edit_other_view_only_access_rules():
    sample = Path("ref_result/project/aa-1.srp")
    payload = sample.read_bytes()

    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "access-project")
        up = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": OWNER},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert up.status_code == 200

        allowed = client.get(f"/projects/{project_id}", params={"user_id": STRANGER})
        assert allowed.status_code == 200

        stranger_list = client.get("/projects", params={"user_id": STRANGER})
        assert stranger_list.status_code == 200
        assert all(x["project_id"] != project_id for x in stranger_list.json()["projects"])

        readonly_upload = client.post(
            f"/projects/{project_id}/files",
            params={"user_id": STRANGER},
            files={"file": ("aa-1.srp", payload, "application/xml")},
        )
        assert readonly_upload.status_code == 403
