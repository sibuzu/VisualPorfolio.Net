from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.project_access import project_dir


OWNER = "550e8400-e29b-41d4-a716-446655447777"
GUEST = "550e8400-e29b-41d4-a716-446655448888"
OTHER = "550e8400-e29b-41d4-a716-446655449999"


def _create_project(client: TestClient, user_id: str, name: str) -> str:
    resp = client.post("/projects", json={"user_id": user_id, "project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _upload_sample_file(client: TestClient, project_id: str, user_id: str, filename: str) -> None:
    payload = Path("ref_result/project/aa-1.srp").read_bytes()
    resp = client.post(
        f"/projects/{project_id}/files",
        params={"user_id": user_id},
        files={"file": (filename, payload, "application/xml")},
    )
    assert resp.status_code == 200


def test_project_download_returns_zip():
    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "zip-download")
        _upload_sample_file(client, project_id, OWNER, "aa-1.srp")

        resp = client.get(f"/projects/{project_id}/download", params={"user_id": GUEST})
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("application/zip")

        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            names = set(zf.namelist())
        assert "aa-1.srp" in names


def test_project_upload_overwrites_dir_and_sets_anonymous():
    with TestClient(app) as client:
        project_id = _create_project(client, OWNER, "zip-upload")
        _upload_sample_file(client, project_id, OWNER, "old.srp")
        assert (project_dir(project_id) / "old.srp").exists()

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("new.txt", "hello")
            zf.writestr("nested/path/data.txt", "world")
        buf.seek(0)

        upload = client.post(
            f"/projects/{project_id}/upload",
            params={"user_id": GUEST},
            data={"project_name": "Uploaded Project"},
            files={"file": ("project.zip", buf.read(), "application/zip")},
        )
        assert upload.status_code == 200
        body = upload.json()
        assert body["ok"] is True
        assert body["user_id"] == "anonymous"
        assert body["project_name"] == "Uploaded Project"

        pdir = project_dir(project_id)
        assert not (pdir / "old.srp").exists()
        assert (pdir / "new.txt").exists()
        assert (pdir / "nested/path/data.txt").exists()

        info = client.get(f"/projects/{project_id}", params={"user_id": OWNER})
        assert info.status_code == 200
        assert info.json()["project"]["user_id"] == "anonymous"
        assert info.json()["project"]["project_name"] == "Uploaded Project"

        listing = client.get("/projects", params={"user_id": OTHER})
        assert listing.status_code == 200
        ids = [x["project_id"] for x in listing.json()["projects"]]
        assert project_id in ids
