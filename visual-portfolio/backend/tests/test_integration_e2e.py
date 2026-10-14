from pathlib import Path
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from backend.main import app


OWNER = "550e8400-e29b-41d4-a716-446655442222"
STRANGER = "550e8400-e29b-41d4-a716-446655449999"


def _create_project(client: TestClient, user_id: str, name: str) -> str:
    resp = client.post("/projects", json={"user_id": user_id, "project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _upload(client: TestClient, project_id: str, user_id: str, filename: str) -> None:
    payload = Path(f"ref_result/project/{filename}").read_bytes()
    resp = client.post(
        f"/projects/{project_id}/files",
        params={"user_id": user_id},
        files={"file": (filename, payload, "application/xml")},
    )
    assert resp.status_code == 200


def _srp_expected(path: Path) -> tuple[float, float]:
    root = ET.parse(path).getroot()
    node = root.find("./策略參數/StgBDSXv5")
    if node is None:
        return 0.0, 0.0
    net = float((node.findtext("累計績效") or "0").strip())
    mdd = abs(float((node.findtext("MaxDrawdown") or "0").strip()))
    return net, mdd


def test_e2e_metric_parity_with_sample_srp():
    sample = Path("ref_result/project/aa-1.srp")
    exp_net, exp_mdd = _srp_expected(sample)

    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "metric-parity")
        _upload(client, project_id, OWNER, "aa-1.srp")

        run = client.post(
            f"/projects/{project_id}/analysis",
            params={"user_id": OWNER},
            json={
                "equities": [
                    {
                        "filename": "aa-1.sea",
                        "active": True,
                        "contract": 1,
                        "weight": 1,
                        "color": "#0a9396",
                        "name": "AA1",
                    }
                ],
                "date_range": {"all": True},
                "options": {
                    "risk_free_rate": 3,
                    "mdd_count": 5,
                    "div_by_count": False,
                    "commission_per_trade": 0,
                },
            },
        )
        assert run.status_code == 200
        body = run.json()

        assert abs(body["summary"]["net_profit"] - exp_net) < 5.0
        assert abs(body["summary"]["mdd"] - exp_mdd) < 5.0
        assert body["summary"]["trade_count"] > 1000
        assert isinstance(body["win_loss"]["month"]["win_prob"], float)
        assert "metrics" in body["diversity"]
        assert isinstance(body["commission"]["years"], list)


def test_e2e_readonly_and_gsea_group_roundtrip():
    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "shared-gsea-group")
        _upload(client, project_id, OWNER, "aa-1.srp")
        _upload(client, project_id, OWNER, "aa-2.srp")

        save = client.put(
            f"/projects/{project_id}/gsea-group",
            params={"user_id": OWNER},
            json={
                "equities": [
                    {"index": 0, "filename": "aa-1.sea", "color": "Blue", "weight": 31.7},
                    {"index": 1, "filename": "aa-2.sea", "color": "Maroon", "weight": 31.7},
                ],
                "dynamic_compounding_config": {
                    "initial_capital": 80000000,
                    "initial_ratio": 0.1,
                    "add_threshold_profit": 100000000,
                    "add_ratio": 0.15,
                    "rollback_amount": 20000000,
                    "max_multiple": 10,
                },
            },
        )
        assert save.status_code == 200

        download = client.get(f"/projects/{project_id}/gsea-group", params={"user_id": OWNER})
        assert download.status_code == 200
        assert '"group"' in download.text
        assert '"project": "aa-1"' in download.text
        assert '"project": "aa-2"' in download.text
        assert '"dynamic_compounding_config"' in download.text
        assert '"initial_capital": 80000000.0' in download.text

        stranger_read = client.get(f"/projects/{project_id}", params={"user_id": STRANGER})
        assert stranger_read.status_code == 200

        stranger_patch = client.patch(
            f"/projects/{project_id}",
            json={"user_id": STRANGER, "project_name": "hijack"},
        )
        assert stranger_patch.status_code == 403

        stranger_gsea_group_put = client.put(
            f"/projects/{project_id}/gsea-group",
            params={"user_id": STRANGER},
            json={"equities": [{"index": 0, "filename": "aa-1.sea", "color": "Blue", "weight": 1}]},
        )
        assert stranger_gsea_group_put.status_code == 403
