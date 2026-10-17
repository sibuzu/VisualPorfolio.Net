import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


OWNER = "550e8400-e29b-41d4-a716-446655443333"
GOLDEN_DIR = Path("backend/tests/golden")


def _create_project(client: TestClient, name: str) -> str:
    resp = client.post("/projects", json={"user_id": OWNER, "project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _upload(client: TestClient, project_id: str, filename: str) -> None:
    payload = Path(f"ref_result/project/{filename}").read_bytes()
    resp = client.post(
        f"/projects/{project_id}/files",
        params={"user_id": OWNER},
        files={"file": (filename, payload, "application/xml")},
    )
    assert resp.status_code == 200


def _round_obj(obj, ndigits=6):
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, list):
        return [_round_obj(x, ndigits) for x in obj]
    if isinstance(obj, dict):
        return {k: _round_obj(v, ndigits) for k, v in obj.items()}
    return obj


def _snapshot_view(body: dict) -> dict:
    return _round_obj(
        {
            "summary": body["summary"],
            "counts": {
                "equity_curve": len(body["equity_curve"]),
                "position_analysis": len(body["position_analysis"]),
                "monthly": len(body["monthly"]),
                "annual": len(body.get("annual", [])),
                "weekly": len(body.get("weekly", [])),
            },
            "equity_curve_head": body["equity_curve"][:30],
            "equity_curve_tail": body["equity_curve"][-30:],
            "position_head": body["position_analysis"][:30],
            "monthly": body["monthly"],
            "annual": body.get("annual", []),
            "weekly": body.get("weekly", []),
            "win_loss": body["win_loss"],
            "commission": body["commission"],
            "diversity": body["diversity"],
            "mdd_markers": body["mdd_markers"],
        }
    )


def _load_expected(name: str) -> dict:
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def test_snapshot_aa1_single_strategy():
    with TestClient(app) as client:
        pid = _create_project(client, "snap-aa1")
        _upload(client, pid, "aa-1.srp")
        resp = client.post(
            f"/projects/{pid}/analysis",
            params={"user_id": OWNER},
            json={
                "equities": [{"filename": "aa-1.srp", "active": True, "contract": 1, "weight": 1, "color": "#0a9396", "name": "AA1"}],
                "date_range": {"all": True},
                "options": {"risk_free_rate": 3, "mdd_count": 5, "div_by_count": False, "commission_per_trade": 0},
            },
        )
        assert resp.status_code == 200
        assert _snapshot_view(resp.json()) == _load_expected("analysis_aa1.json")


def test_snapshot_aa1_aa2_combo_div_by_count():
    with TestClient(app) as client:
        pid = _create_project(client, "snap-combo")
        _upload(client, pid, "aa-1.srp")
        _upload(client, pid, "aa-2.srp")
        resp = client.post(
            f"/projects/{pid}/analysis",
            params={"user_id": OWNER},
            json={
                "equities": [
                    {"filename": "aa-1.srp", "active": True, "contract": 2, "weight": 1.1, "color": "#0a9396", "name": "AA1"},
                    {"filename": "aa-2.srp", "active": True, "contract": 1, "weight": 0.8, "color": "#bb3e03", "name": "AA2"},
                ],
                "date_range": {"all": True},
                "options": {"risk_free_rate": 3, "mdd_count": 5, "div_by_count": True, "commission_per_trade": 0},
            },
        )
        assert resp.status_code == 200
        assert _snapshot_view(resp.json()) == _load_expected("analysis_aa1_aa2_divcount.json")
