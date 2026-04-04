from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.project_access import project_dir


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


def _upload_sample_file(client: TestClient, project_id: str, filename: str) -> None:
    payload = Path("ref_result/project/aa-1.srp").read_bytes()
    resp = client.post(
        f"/projects/{project_id}/files",
        files={"file": (filename, payload, "application/xml")},
    )
    assert resp.status_code == 200


def _make_gsea_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("new.txt", "hello")
        zf.writestr("nested/path/data.txt", "world")
    return buf.getvalue()


def _make_gsea_with_root_dir_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("BatchRun/strategy.toml", "[strategy]\nname='BatchRun'\n")
        zf.writestr("BatchRun/group.json", '{"group":[{"project":"BatchRun-1"}]}')
        zf.writestr("BatchRun/BatchRun-1.sea", b"dummy")
    return buf.getvalue()


def _make_group_weight_count_gsea_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("BatchRun/strategy.toml", "[strategy]\nname='BatchRun'\n")
        zf.writestr(
            "BatchRun/group.json",
            """
            {
              "group": [
                {"project":"BatchRun-1","count":3,"weight":"2.5","metadata":{"color":"Maroon"}}
              ]
            }
            """,
        )
        zf.writestr("BatchRun/BatchRun-1.sea", b"dummy")
    return buf.getvalue()


def test_project_download_returns_zip():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "zip-download")
        _upload_sample_file(client, project_id, "aa-1.srp")

        resp = client.get(f"/projects/{project_id}/download")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("application/zip")
        assert ".gsea" in str(resp.headers.get("content-disposition", ""))

        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            names = set(zf.namelist())
        assert "aa-1.sea" in names
        assert "project.pfo" not in names


def test_project_download_allowed_for_non_owner_viewer():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        other_id, other_pw = _new_user("other")

        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "zip-download-forbid")
        _upload_sample_file(client, project_id, "old.srp")

        _signup_and_login(client, other_id, other_pw)
        allow = client.get(f"/projects/{project_id}/download")
        assert allow.status_code == 200
        assert allow.headers.get("content-type", "").startswith("application/zip")


def test_project_upload_overwrites_dir_and_keeps_current_owner():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "zip-upload")
        _upload_sample_file(client, project_id, "old.srp")
        assert (project_dir(project_id) / "old.sea").exists()
        zip_payload = _make_gsea_bytes()

        upload = client.post(
            f"/projects/{project_id}/upload",
            data={"project_name": "Uploaded Project"},
            files={"file": ("project.gsea", zip_payload, "application/zip")},
        )
        assert upload.status_code == 200
        body = upload.json()
        assert body["ok"] is True
        assert body["user_id"] == owner_id
        assert body["project_name"] == "Uploaded Project"

        pdir = project_dir(project_id)
        assert not (pdir / "old.sea").exists()
        assert (pdir / "new.txt").exists()
        assert (pdir / "nested/path/data.txt").exists()

        info = client.get(f"/projects/{project_id}")
        assert info.status_code == 200
        assert info.json()["project"]["user_id"] == owner_id
        assert info.json()["project"]["project_name"] == "Uploaded Project"


def test_project_upload_rejects_zip_extension():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "gsea-upload")
        zip_payload = _make_gsea_bytes()

        upload = client.post(
            f"/projects/{project_id}/upload",
            data={"project_name": "Uploaded GSEA"},
            files={"file": ("project.zip", zip_payload, "application/zip")},
        )
    assert upload.status_code == 400
    assert upload.json()["detail"] == "Only .gsea is supported"


def test_project_upload_strips_single_root_folder():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "gsea-root-folder")
        payload = _make_gsea_with_root_dir_bytes()

        upload = client.post(
            f"/projects/{project_id}/upload",
            data={"project_name": "RootFolder"},
            files={"file": ("BatchRun.gsea", payload, "application/zip")},
        )
        assert upload.status_code == 200

        pdir = project_dir(project_id)
        assert (pdir / "strategy.toml").exists()
        assert (pdir / "group.json").exists()
        assert (pdir / "BatchRun-1.sea").exists()


def test_project_upload_fails_when_project_belongs_to_other_user():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        other_id, other_pw = _new_user("other")

        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "zip-upload-owner-check")
        _upload_sample_file(client, project_id, "old.srp")

        _signup_and_login(client, other_id, other_pw)
        zip_payload = _make_gsea_bytes()
        upload = client.post(
            f"/projects/{project_id}/upload",
            data={"project_name": "Not Allowed"},
            files={"file": ("project.gsea", zip_payload, "application/zip")},
        )
        assert upload.status_code == 403
        assert upload.json()["detail"] == "Project already owned by another user"


def test_project_upload_keeps_group_weight_count():
    with TestClient(app) as client:
        owner_id, owner_pw = _new_user("owner")
        _signup_and_login(client, owner_id, owner_pw)
        project_id = _create_project(client, "gsea-pfo-group")
        payload = _make_group_weight_count_gsea_bytes()

        upload = client.post(
            f"/projects/{project_id}/upload",
            data={"project_name": "GroupPfo"},
            files={"file": ("BatchRun.gsea", payload, "application/zip")},
        )
        assert upload.status_code == 200

        group_path = project_dir(project_id) / "group.json"
        assert group_path.exists()
        data = json.loads(group_path.read_text(encoding="utf-8"))
        item = data["group"][0]
        assert item["count"] == 3
        assert item["weight"] == "2.5"
        assert not (project_dir(project_id) / "project.pfo").exists()
