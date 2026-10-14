from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from .analysis import CalculationSettings, analyze_report
from .auth import require_user, router as auth_router
from .importer import MAX_UPLOAD_BYTES, ReportFormatError, parse_report


app = FastAPI(title="Strategy Report API", version="0.1.0")
app.include_router(auth_router)


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
            return analyze_report(source, cfg)
        except ReportFormatError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
