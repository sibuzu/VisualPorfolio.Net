from pathlib import Path
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from backend.main import app


OWNER = "550e8400-e29b-41d4-a716-446655442222"
STRANGER = "550e8400-e29b-41d4-a716-446655449999"


def _create_project(client: TestClient, guest_id: str, name: str) -> str:
    resp = client.post("/projects", json={"guest_id": guest_id, "project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _upload(client: TestClient, project_id: str, guest_id: str, filename: str) -> None:
    payload = Path(f"ref_result/project/{filename}").read_bytes()
    resp = client.post(
        f"/projects/{project_id}/files",
        params={"guest_id": guest_id},
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
            params={"guest_id": OWNER},
            json={
                "equities": [
                    {
                        "filename": "aa-1.srp",
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


def test_e2e_readonly_and_pfo_roundtrip():
    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "shared-pfo")
        _upload(client, project_id, OWNER, "aa-1.srp")
        _upload(client, project_id, OWNER, "aa-2.srp")

        save = client.put(
            f"/projects/{project_id}/pfo",
            params={"guest_id": OWNER},
            json={
                "equities": [
                    {"index": 0, "filename": "aa-1.srp", "color": "Blue", "weight": 31.7},
                    {"index": 1, "filename": "aa-2.srp", "color": "Maroon", "weight": 31.7},
                ]
            },
        )
        assert save.status_code == 200

        download = client.get(f"/projects/{project_id}/pfo", params={"guest_id": OWNER})
        assert download.status_code == 200
        assert "PortfolioyList" in download.text
        assert "aa-1.srp" in download.text
        assert "aa-2.srp" in download.text

        stranger_read = client.get(f"/projects/{project_id}", params={"guest_id": STRANGER})
        assert stranger_read.status_code == 200

        stranger_patch = client.patch(
            f"/projects/{project_id}",
            json={"guest_id": STRANGER, "project_name": "hijack"},
        )
        assert stranger_patch.status_code == 403

        stranger_pfo_put = client.put(
            f"/projects/{project_id}/pfo",
            params={"guest_id": STRANGER},
            json={"equities": [{"index": 0, "filename": "aa-1.srp", "color": "Blue", "weight": 1}]},
        )
        assert stranger_pfo_put.status_code == 403
