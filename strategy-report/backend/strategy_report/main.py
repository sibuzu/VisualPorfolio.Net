from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from .analysis import CalculationSettings, analyze_report
from .importer import MAX_UPLOAD_BYTES, ReportFormatError, parse_report


app = FastAPI(title="Strategy Report API", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/report")
async def create_report(file: UploadFile = File(...), settings: str = Form("{}")) -> dict:
    try:
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
    finally:
        await file.close()
