from __future__ import annotations

import shutil

from fastapi import APIRouter, Body, HTTPException, Query

from backend.models.project import ProjectCreateRequest, ProjectListResponse, ProjectPatchRequest
from backend.services.project_access import (
    create_project,
    get_project_access,
    list_projects_for_guest,
    project_dir,
    touch_access_time,
    update_project,
)
from backend.db.database import get_conn

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
def list_projects(guest_id: str = Query(..., min_length=8)):
    projects = list_projects_for_guest(guest_id)
    return {"projects": projects}


@router.post("")
def post_project(payload: ProjectCreateRequest):
    project = create_project(payload.guest_id, payload.project_name)
    return {"project_id": project["project_id"], "project": project}


@router.get("/{project_id}")
def get_project(project_id: str, guest_id: str = Query(..., min_length=8)):
    project, _ = get_project_access(project_id, guest_id)
    touch_access_time(project_id)
    return {"project": project}


@router.patch("/{project_id}")
def patch_project(project_id: str, payload: ProjectPatchRequest):
    project = update_project(project_id, payload.guest_id, payload.project_name, payload.shared)
    return {"project": project}


@router.delete("/{project_id}")
def delete_project(project_id: str, guest_id: str = Query(..., min_length=8)):
    project, access = get_project_access(project_id, guest_id)
    if access != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete")

    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()

    shutil.rmtree(project_dir(project_id), ignore_errors=True)
    return {"deleted": True, "project_id": project_id, "project_name": project["project_name"]}
