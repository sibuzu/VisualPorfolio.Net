from fastapi.testclient import TestClient

from backend.main import app


def test_create_and_list_project():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    with TestClient(app) as client:
        create = client.post("/projects", json={"user_id": user_id, "project_name": "p1"})
        assert create.status_code == 200
        pid = create.json()["project_id"]

        listing = client.get("/projects", params={"user_id": user_id})
        assert listing.status_code == 200
        ids = [x["project_id"] for x in listing.json()["projects"]]
        assert pid in ids
