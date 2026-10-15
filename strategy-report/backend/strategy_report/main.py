from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, ValidationError
from starlette.datastructures import UploadFile
from starlette.concurrency import run_in_threadpool

from .analysis import CalculationSettings, analyze_report
from .auth import require_user, router as auth_router
from .buy_hold import analyze_buy_hold
from .importer import MAX_UPLOAD_BYTES, ReportFormatError, parse_report
from .storage import (
    copy_performance, create_performance, delete_performance, get_performance,
    initialize_storage, list_important_performances, list_performances, save_settings, update_performance,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_storage()
    yield


app = FastAPI(title="Strategy Report API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)


def analyze_with_reference(source, settings: CalculationSettings) -> dict:
    result = analyze_report(source, settings)
    result["buy_hold"] = analyze_buy_hold(source, settings.buy_hold, settings.date_start, settings.date_end)
    return result


class PerformancePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    important: bool | None = None


class PerformanceCopy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/report")
async def create_report(request: Request, _: str = Depends(require_user)) -> dict:
    async with request.form(max_files=1, max_fields=1) as form:
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(status_code=422, detail="A report file is required")
        settings = form.get("settings", "{}")
        if not isinstance(settings, str):
            raise HTTPException(status_code=422, detail="Invalid settings")
        try:
            cfg = CalculationSettings.model_validate_json(settings)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors(include_input=False)) from exc
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Report exceeds 20 MiB upload limit")
        try:
            source = parse_report(file.filename or "", content)
            return await run_in_threadpool(analyze_with_reference, source, cfg)
        except ReportFormatError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/performances")
def performances(user_id: str = Depends(require_user)) -> dict:
    return {"performances": list_performances(user_id)}


@app.get("/api/performances/important")
def important_performances(user_id: str = Depends(require_user)) -> dict:
    return {"performances": list_important_performances(user_id)}


@app.post("/api/performances", status_code=201)
async def post_performance(request: Request, response: Response, user_id: str = Depends(require_user)) -> dict:
    async with request.form(max_files=1, max_fields=1) as form:
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(status_code=422, detail="A report file is required")
        name = form.get("name", "")
        if not isinstance(name, str):
            raise HTTPException(status_code=422, detail="Invalid performance name")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Report exceeds 20 MiB upload limit")
        try:
            source = parse_report(file.filename or "", content)
        except ReportFormatError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        item, created = create_performance(user_id, content, source, name)
        if not created:
            response.status_code = 200
        return {"performance": item, "created": created}


@app.get("/api/performances/{item_id}")
def performance(item_id: str, user_id: str = Depends(require_user)) -> dict:
    item, _ = get_performance(user_id, item_id)
    return {"performance": item}


@app.post("/api/performances/{item_id}/copy", status_code=201)
def duplicate_performance(item_id: str, payload: PerformanceCopy, user_id: str = Depends(require_user)) -> dict:
    return {"performance": copy_performance(user_id, item_id, payload.name)}


@app.get("/api/performances/{item_id}/download")
def download_performance(item_id: str, user_id: str = Depends(require_user)) -> Response:
    item, content = get_performance(user_id, item_id, include_content=True)
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f'source.{item["source_format"]}', content or b"")
        archive.writestr("performance.json", json.dumps(item, ensure_ascii=False, indent=2))
    return Response(content=output.getvalue(), media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{item_id}.zip"'
    })


@app.patch("/api/performances/{item_id}")
def patch_performance(item_id: str, payload: PerformancePatch, user_id: str = Depends(require_user)) -> dict:
    return {"performance": update_performance(user_id, item_id, name=payload.name, important=payload.important)}


@app.delete("/api/performances/{item_id}")
def remove_performance(item_id: str, user_id: str = Depends(require_user)) -> dict:
    delete_performance(user_id, item_id)
    return {"deleted": True, "performance_id": item_id}


@app.post("/api/performances/{item_id}/report")
def calculate_performance(item_id: str, settings: CalculationSettings, user_id: str = Depends(require_user)) -> dict:
    item, content = get_performance(user_id, item_id, include_content=True)
    try:
        source = parse_report(item["filename"], content or b"")
        result = analyze_with_reference(source, settings)
    except ReportFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    save_settings(user_id, item_id, settings)
    return result
