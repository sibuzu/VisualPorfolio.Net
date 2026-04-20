from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DynamicCompoundingConfig:
    initial_capital: float = 80_000_000.0
    initial_ratio: float = 0.10
    add_threshold_profit: float = 100_000_000.0
    add_ratio: float = 0.15
    rollback_amount: float = 20_000_000.0
    max_multiple: float = 10.0


def _safe_float(v: object, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def normalize_dynamic_compounding_config(raw: dict | None) -> DynamicCompoundingConfig:
    raw = raw if isinstance(raw, dict) else {}
    cfg = DynamicCompoundingConfig(
        initial_capital=max(_safe_float(raw.get("initial_capital"), 80_000_000.0), 1.0),
        initial_ratio=max(_safe_float(raw.get("initial_ratio"), 0.10), 0.0),
        add_threshold_profit=_safe_float(raw.get("add_threshold_profit"), 100_000_000.0),
        add_ratio=max(_safe_float(raw.get("add_ratio"), 0.15), 0.0),
        rollback_amount=max(_safe_float(raw.get("rollback_amount"), 20_000_000.0), 0.0),
        max_multiple=max(_safe_float(raw.get("max_multiple"), 10.0), 0.0),
    )
    return cfg


def _dt(text: str) -> datetime:
    return datetime.strptime(str(text)[:10], "%Y-%m-%d")


def _weekly_periods(trades: list[dict]) -> list[dict]:
    rows: list[dict] = []
    cur_key = None
    cur_profit = 0.0
    cur_end = ""
    for t in trades:
        d = _dt(str(t["trade_date2"]))
        key = d.date().toordinal() - ((d.weekday() + 1) % 7)
        p = float(t.get("net_profit", 0.0))
        ds = d.strftime("%Y-%m-%d")
        if key != cur_key:
            if cur_key is not None:
                rows.append({"end_date": cur_end, "profit": cur_profit})
            cur_key = key
            cur_profit = p
            cur_end = ds
        else:
            cur_profit += p
            cur_end = ds
    if cur_key is not None:
        rows.append({"end_date": cur_end, "profit": cur_profit})
    return rows


def _monthly_periods(trades: list[dict]) -> list[dict]:
    rows: list[dict] = []
    cur_key = None
    cur_profit = 0.0
    cur_end = ""
    for t in trades:
        d = _dt(str(t["trade_date2"]))
        key = d.year * 100 + d.month
        p = float(t.get("net_profit", 0.0))
        ds = d.strftime("%Y-%m-%d")
        if key != cur_key:
            if cur_key is not None:
                rows.append({"end_date": cur_end, "profit": cur_profit})
            cur_key = key
            cur_profit = p
            cur_end = ds
        else:
            cur_profit += p
            cur_end = ds
    if cur_key is not None:
        rows.append({"end_date": cur_end, "profit": cur_profit})
    return rows


def _simulate(periods: list[dict], cfg: DynamicCompoundingConfig) -> dict:
    initial = float(cfg.initial_capital)
    if initial <= 0:
        initial = 1.0
    cap_limit = max(float(cfg.max_multiple), 0.0) * initial

    equity = initial
    peak = initial
    mdd_amount = 0.0
    ratio = max(float(cfg.initial_ratio), 0.0)
    mode = "initial"
    has_entered_add = False
    waiting_recovery = False
    recovery_peak = initial
    reach_10x_date = ""
    next_mode = mode

    for row in periods:
        if next_mode != mode:
            mode = next_mode
            ratio = max(float(cfg.add_ratio if mode == "add" else cfg.initial_ratio), 0.0)

        trading_capital = equity * ratio
        if cap_limit > 0:
            trading_capital = min(trading_capital, cap_limit)
        profit = float(row.get("profit", 0.0))
        period_pnl = profit * (trading_capital / initial)
        equity += period_pnl

        if equity > peak:
            peak = equity
        dd = max(peak - equity, 0.0)
        if dd > mdd_amount:
            mdd_amount = dd

        if not reach_10x_date and equity >= initial * 10.0:
            reach_10x_date = str(row.get("end_date", ""))

        next_mode = mode
        if mode == "initial":
            if waiting_recovery:
                if equity > recovery_peak:
                    next_mode = "add"
                    waiting_recovery = False
            elif (not has_entered_add) and (equity - initial > float(cfg.add_threshold_profit)):
                next_mode = "add"
                has_entered_add = True
        else:
            if peak - equity > float(cfg.rollback_amount):
                next_mode = "initial"
                waiting_recovery = True
                recovery_peak = peak

    first_date = str(periods[0]["end_date"]) if periods else ""
    last_date = str(periods[-1]["end_date"]) if periods else ""
    years = 0.0
    if first_date and last_date:
        t1 = _dt(first_date)
        t2 = _dt(last_date)
        years = max(((t2 - t1).days + 1) / 365.25, 1e-9)

    multiple = equity / initial if initial > 0 else 0.0
    if years > 0 and initial > 0 and equity > 0:
        cagr_pct = (multiple ** (1.0 / years) - 1.0) * 100.0
    elif equity <= 0:
        cagr_pct = -100.0
    else:
        cagr_pct = 0.0

    mdd_pct = (mdd_amount / peak) * 100.0 if peak > 0 else 0.0
    return {
        "initial_net_value": round(initial, 6),
        "final_net_value": round(equity, 6),
        "profit_multiple": round(multiple, 6),
        "cagr_pct": round(cagr_pct, 6),
        "mdd_pct": round(mdd_pct, 6),
        "mdd_amount": round(mdd_amount, 6),
        "reach_10x_date": reach_10x_date or "未達成",
    }


def build_dynamic_compounding(trades: list[dict], config: DynamicCompoundingConfig) -> dict:
    weekly_periods = _weekly_periods(trades)
    monthly_periods = _monthly_periods(trades)
    return {
        "weekly": _simulate(weekly_periods, config),
        "monthly": _simulate(monthly_periods, config),
    }
