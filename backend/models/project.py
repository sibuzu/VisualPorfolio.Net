from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    user_id: str = Field(min_length=8)
    project_name: str = Field(min_length=1, max_length=120)


class ProjectPatchRequest(BaseModel):
    user_id: str = Field(min_length=8)
    project_name: str | None = Field(default=None, min_length=1, max_length=120)


class ProjectCopyRequest(BaseModel):
    user_id: str = Field(min_length=8)
    project_name: str = Field(min_length=1, max_length=120)


class ProjectResponse(BaseModel):
    project_id: str
    user_id: str
    project_name: str
    create_time: datetime
    access_time: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
