from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.commission import CommissionCfg, build_commission
from backend.services.diversity import build_diversity
from backend.services.parser import parse_file
from backend.services.portfolio import merge_trades
from backend.services.project_access import get_project_access, project_dir, touch_access_time
from backend.services.summary_report import build_report
from backend.services.win_loss import build_win_loss

router = APIRouter(prefix="/projects/{project_id}/analysis", tags=["analysis"])


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
    capital: float = 100.0
    risk_free_rate: float = 0.0
    mdd_count: int = Field(default=5, ge=1, le=20)
    div_by_count: bool = False
    commission_per_trade: float = 0.0
    commission_config: dict[str, float] | None = None


class AnalysisRequest(BaseModel):
    equities: list[EquityConfig] = Field(default_factory=list)
    date_range: DateRange = DateRange()
    options: Options = Options()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


@router.post("")
def run_analysis(project_id: str, payload: AnalysisRequest, guest_id: str = Query(..., min_length=8)):
    get_project_access(project_id, guest_id)

    if not payload.equities:
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

    folder = project_dir(project_id)
    strategy_trades: list[tuple[list, dict]] = []

    for i, eq in enumerate(payload.equities):
        if not eq.active:
            continue
        file_path = folder / eq.filename
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

    return {
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
