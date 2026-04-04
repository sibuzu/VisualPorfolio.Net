from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.services.commission import CommissionCfg, build_commission
from backend.services.auth import require_auth
from backend.services.diversity import build_diversity
from backend.services.parser import parse_file
from backend.services.portfolio import merge_trades
from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.summary_report import build_report
from backend.services.win_loss import build_win_loss

router = APIRouter(prefix="/projects/{project_id}/analysis", tags=["analysis"])
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis-job")
_jobs_lock = Lock()
_jobs: dict[str, dict] = {}
_JOB_TTL_HOURS = 24


class EquityConfig(BaseModel):
    filename: str
    active: bool = True
    contract: float = 1.0
    weight: float = 1.0
    color: str = "#0000FF"
    name: str = ""


class DateRange(BaseModel):
    start: str | None = None
    end: str | None = None
    all: bool = True


class Options(BaseModel):
    capital: float = 1_000_000.0
    risk_free_rate: float = 0.0
    mdd_count: int = Field(default=5, ge=1, le=20)
    div_by_count: bool = False
    commission_per_trade: float = 0.0
    commission_config: dict[str, float] | None = None


class AnalysisRequest(BaseModel):
    equities: list[EquityConfig] = Field(default_factory=list)
    date_range: DateRange = DateRange()
    options: Options = Options()


def _empty_analysis() -> dict:
    return {
        "summary": {},
        "equity_curve": [],
        "monthly": [],
        "annual": [],
        "weekly": [],
        "position_analysis": [],
        "win_loss": {},
        "commission": {},
        "diversity": {},
        "mdd_markers": [],
    }


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def _build_analysis(project_id: str, payload: AnalysisRequest) -> dict:
    if not payload.equities:
        return _empty_analysis()

    folder = project_dir(project_id)
    strategy_trades: list[tuple[list, dict]] = []

    for i, eq in enumerate(payload.equities):
        if not eq.active:
            continue
        file_path = folder / eq.filename
        if not file_path.exists() and Path(eq.filename).suffix.lower() in {".srp", ".xrp", ".xml"}:
            alt = folder / f"{Path(eq.filename).stem}.sea"
            if alt.exists():
                file_path = alt
        if not file_path.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {eq.filename}")
        trades = parse_file(file_path, strategy_index=i)
        strategy_trades.append((trades, eq.model_dump()))

    active_contract_sum = sum(max(float(eq.contract), 0.0) for eq in payload.equities if eq.active)
    factor = (1.0 / active_contract_sum) if payload.options.div_by_count and active_contract_sum > 0 else 1.0

    start = None if payload.date_range.all else _parse_date(payload.date_range.start)
    end = None if payload.date_range.all else _parse_date(payload.date_range.end)
    merged = merge_trades(strategy_trades, start, end, factor=factor)

    report = build_report(
        merged,
        risk_free_rate=payload.options.risk_free_rate,
        mdd_count=payload.options.mdd_count,
        capital=payload.options.capital,
    )

    position_analysis = [
        {
            "strategy_index": t["strategy_index"],
            "side": t["bs"],
            "entry": t["trade_date1"],
            "exit": t["trade_date2"],
            "pnl": round(float(t["net_profit"]), 6),
        }
        for t in merged
    ]

    touch_access_time(project_id)

    commission_cfg = None
    if payload.options.commission_config:
        cfg = payload.options.commission_config
        commission_cfg = CommissionCfg(
            ref_capital=float(cfg.get("ref_capital", 840.0)),
            init_capital=float(cfg.get("init_capital", 840.0)),
            leverage=float(cfg.get("leverage", 3.0)),
            fee_rate=float(cfg.get("fee_rate", 0.05)),
            rebate_rate=float(cfg.get("rebate_rate", 50.0)),
            quarter_share_rate=float(cfg.get("quarter_share_rate", 30.0)),
            bonus_thresholds=(
                float(cfg.get("bonus_threshold1", 100.0)),
                float(cfg.get("bonus_threshold2", 150.0)),
                float(cfg.get("bonus_threshold3", 200.0)),
                float(cfg.get("bonus_threshold4", 0.0)),
            ),
            bonus_rates=(
                float(cfg.get("bonus_rate1", 10.0)),
                float(cfg.get("bonus_rate2", 20.0)),
                float(cfg.get("bonus_rate3", 30.0)),
                float(cfg.get("bonus_rate4", 0.0)),
            ),
        )

    result = {
        "summary": report["summary"],
        "equity_curve": report["equity_curve"],
        "monthly": report["monthly"],
        "annual": report.get("annual", []),
        "weekly": report.get("weekly", []),
        "position_analysis": position_analysis,
        "win_loss": build_win_loss(merged),
        "commission": build_commission(merged, payload.options.commission_per_trade, cfg=commission_cfg),
        "diversity": build_diversity(merged),
        "mdd_markers": report["mdd_markers"],
    }
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _prune_jobs() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_JOB_TTL_HOURS)
    with _jobs_lock:
        stale = []
        for jid, job in _jobs.items():
            status = str(job.get("status", ""))
            if status not in {"done", "failed"}:
                continue
            ts = job.get("finished_at") or job.get("updated_at") or job.get("created_at")
            try:
                dt = datetime.fromisoformat(str(ts))
            except Exception:
                stale.append(jid)
                continue
            if dt < cutoff:
                stale.append(jid)
        for jid in stale:
            _jobs.pop(jid, None)


def _run_job(job_id: str, project_id: str, payload_data: dict) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["status"] = "running"
        job["updated_at"] = _now_iso()

    try:
        payload = AnalysisRequest.model_validate(payload_data)
        result = _build_analysis(project_id, payload)
    except HTTPException as e:
        with _jobs_lock:
            job = _jobs.get(job_id)
            if job:
                job["status"] = "failed"
                job["error"] = str(e.detail)
                job["updated_at"] = _now_iso()
                job["finished_at"] = _now_iso()
        return
    except Exception as e:
        with _jobs_lock:
            job = _jobs.get(job_id)
            if job:
                job["status"] = "failed"
                job["error"] = str(e)
                job["updated_at"] = _now_iso()
                job["finished_at"] = _now_iso()
        return

    with _jobs_lock:
        job = _jobs.get(job_id)
        if job:
            job["status"] = "done"
            job["result"] = result
            job["updated_at"] = _now_iso()
            job["finished_at"] = _now_iso()


def _get_job_or_404(project_id: str, job_id: str, current_user: str) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.get("user_id") != current_user:
        raise HTTPException(status_code=403, detail="Analysis job is owned by another user")
    return job


@router.post("")
def run_analysis(project_id: str, payload: AnalysisRequest, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    result = _build_analysis(project_id, payload)
    touch_access_time(project_id)
    return result


@router.post("/jobs")
def create_analysis_job(project_id: str, payload: AnalysisRequest, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    _prune_jobs()

    job_id = uuid4().hex
    now = _now_iso()
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "project_id": project_id,
            "user_id": current_user,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "finished_at": None,
            "error": "",
            "result": None,
        }

    _executor.submit(_run_job, job_id, project_id, payload.model_dump())
    touch_access_time(project_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_analysis_job(project_id: str, job_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    _prune_jobs()
    job = _get_job_or_404(project_id, job_id, current_user)
    touch_access_time(project_id)
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "error": job.get("error", ""),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "finished_at": job.get("finished_at"),
    }


@router.get("/jobs/{job_id}/result")
def get_analysis_job_result(project_id: str, job_id: str, current_user: str = Depends(require_auth)):
    get_project_access(project_id, current_user)
    _prune_jobs()
    job = _get_job_or_404(project_id, job_id, current_user)
    status = job.get("status")
    if status == "failed":
        raise HTTPException(status_code=400, detail=job.get("error") or "Analysis job failed")
    if status != "done":
        raise HTTPException(status_code=409, detail="Analysis job not completed")
    touch_access_time(project_id)
    return job.get("result") or _empty_analysis()
