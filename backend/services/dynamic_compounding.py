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
    rollback_percent: float = 0.0
    max_multiple: float = 10.0
    base_mdd: float = 0.0


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
        rollback_percent=max(_safe_float(raw.get("rollback_percent"), 0.0), 0.0),
        max_multiple=max(_safe_float(raw.get("max_multiple"), 10.0), 0.0),
        base_mdd=max(_safe_float(raw.get("base_mdd"), 0.0), 0.0),
    )
    return cfg


def _dt(text: str) -> datetime:
    return datetime.strptime(str(text)[:10], "%Y-%m-%d")


def _iso_week_key(date_text: str) -> tuple[int, int]:
    d = _dt(date_text)
    iso = d.isocalendar()
    return int(iso.year), int(iso.week)


def _weekly_periods(trades: list[dict]) -> list[dict]:
    rows: list[dict] = []
    cur_key = None
    cur_profit = 0.0
    cur_end = ""
    cur_profits: list[float] = []
    cur_points: list[dict] = []
    for t in trades:
        d = _dt(str(t["trade_date2"]))
        iso = d.isocalendar()
        key = (int(iso.year), int(iso.week))
        p = float(t.get("net_profit", 0.0))
        ds = d.strftime("%Y-%m-%d")
        if key != cur_key:
            if cur_key is not None:
                rows.append(
                    {
                        "end_date": cur_end,
                        "profit": cur_profit,
                        "profits": cur_profits,
                        "points": cur_points,
                    }
                )
            cur_key = key
            cur_profit = p
            cur_end = ds
            cur_profits = [p]
            cur_points = [{"date": ds, "profit": p}]
        else:
            cur_profit += p
            cur_end = ds
            cur_profits.append(p)
            cur_points.append({"date": ds, "profit": p})
    if cur_key is not None:
        rows.append(
            {
                "end_date": cur_end,
                "profit": cur_profit,
                "profits": cur_profits,
                "points": cur_points,
            }
        )
    return rows


def _monthly_periods(trades: list[dict]) -> list[dict]:
    rows: list[dict] = []
    cur_key = None
    cur_profit = 0.0
    cur_end = ""
    cur_profits: list[float] = []
    cur_points: list[dict] = []
    for t in trades:
        d = _dt(str(t["trade_date2"]))
        key = d.year * 100 + d.month
        p = float(t.get("net_profit", 0.0))
        ds = d.strftime("%Y-%m-%d")
        if key != cur_key:
            if cur_key is not None:
                rows.append(
                    {
                        "end_date": cur_end,
                        "profit": cur_profit,
                        "profits": cur_profits,
                        "points": cur_points,
                    }
                )
            cur_key = key
            cur_profit = p
            cur_end = ds
            cur_profits = [p]
            cur_points = [{"date": ds, "profit": p}]
        else:
            cur_profit += p
            cur_end = ds
            cur_profits.append(p)
            cur_points.append({"date": ds, "profit": p})
    if cur_key is not None:
        rows.append(
            {
                "end_date": cur_end,
                "profit": cur_profit,
                "profits": cur_profits,
                "points": cur_points,
            }
        )
    return rows


def _simulate(
    periods: list[dict],
    cfg: DynamicCompoundingConfig,
    *,
    cagr_start_date: str = "",
    cagr_end_date: str = "",
) -> dict:
    initial = float(cfg.initial_capital)
    if initial <= 0:
        initial = 1.0
    # base_pnl scale baseline:
    # when provided, use reference MDD from report (e.g. 800萬) as denominator.
    # fallback keeps legacy behavior.
    baseline_capital = float(cfg.base_mdd)
    if baseline_capital <= 0:
        baseline_capital = initial * max(float(cfg.initial_ratio), 0.0)
    if baseline_capital <= 0:
        baseline_capital = initial
    # mdd-aligned cap:
    # exposure cap is max_multiple times baseline exposure (not initial capital).
    initial_risk_capital = initial * max(float(cfg.initial_ratio), 0.0)
    if initial_risk_capital <= 0:
        initial_risk_capital = baseline_capital
    cap_limit = max(float(cfg.max_multiple), 0.0) * initial_risk_capital

    equity = initial
    logic_peak = initial
    mdd_peak = initial
    mdd_amount = 0.0
    mdd_pct_max = 0.0
    mdd_amount_date = ""
    mdd_pct_date = ""
    ratio = max(float(cfg.initial_ratio), 0.0)
    mode = "initial"
    has_entered_add = False
    waiting_recovery = False
    recovery_peak = initial
    reach_10x_date = ""
    reach_max_multiple_date = ""
    next_mode = mode
    curve: list[dict] = []
    rollback_adjust_count = 0
    sample_week_key: tuple[int, int] | None = None
    sample_last_date = ""
    sample_last_equity = initial

    def _update_mdd(point_date: str) -> None:
        nonlocal mdd_peak, mdd_amount, mdd_pct_max, mdd_amount_date, mdd_pct_date
        dd = max(mdd_peak - equity, 0.0)
        if dd > mdd_amount:
            mdd_amount = dd
            mdd_amount_date = point_date
        if mdd_peak > 0:
            dd_pct = (dd / mdd_peak) * 100.0
            if dd_pct > mdd_pct_max:
                mdd_pct_max = dd_pct
                mdd_pct_date = point_date
        if equity > mdd_peak:
            mdd_peak = equity

    def _flush_week_sample() -> None:
        if not sample_last_date:
            return
        dd = max(mdd_peak - sample_last_equity, 0.0)
        curve.append(
            {
                "date": sample_last_date,
                "net_value": round(sample_last_equity, 6),
                "drawdown_amount": round(dd, 6),
            }
        )

    for row in periods:
        if next_mode != mode:
            mode = next_mode
            ratio = max(float(cfg.add_ratio if mode == "add" else cfg.initial_ratio), 0.0)

        raw_trading_capital = equity * ratio
        if (
            not reach_max_multiple_date
            and cap_limit > 0
            and raw_trading_capital >= cap_limit
        ):
            reach_max_multiple_date = str(row.get("end_date", ""))
        trading_capital = raw_trading_capital
        if cap_limit > 0:
            trading_capital = min(trading_capital, cap_limit)
        points = row.get("points")
        if isinstance(points, list) and points:
            for item in points:
                point_date = str(item.get("date", row.get("end_date", "")))
                point_week = _iso_week_key(point_date) if point_date else None
                raw_p = float(item.get("profit", 0.0))
                if point_week is not None:
                    if sample_week_key is None:
                        sample_week_key = point_week
                    elif point_week != sample_week_key:
                        _flush_week_sample()
                        sample_week_key = point_week
                step_pnl = raw_p * (trading_capital / baseline_capital)
                equity += step_pnl
                if equity > logic_peak:
                    logic_peak = equity
                _update_mdd(point_date)
                if point_week is not None:
                    sample_last_date = point_date
                    sample_last_equity = equity
        else:
            profit = float(row.get("profit", 0.0))
            point_date = str(row.get("end_date", ""))
            point_week = _iso_week_key(point_date) if point_date else None
            if point_week is not None:
                if sample_week_key is None:
                    sample_week_key = point_week
                elif point_week != sample_week_key:
                    _flush_week_sample()
                    sample_week_key = point_week
            period_pnl = profit * (trading_capital / baseline_capital)
            equity += period_pnl
            if equity > logic_peak:
                logic_peak = equity
            _update_mdd(point_date)
            if point_week is not None:
                sample_last_date = point_date
                sample_last_equity = equity

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
            rollback_threshold = float(cfg.rollback_amount)
            if float(cfg.rollback_percent) > 0:
                rollback_threshold = logic_peak * float(cfg.rollback_percent)
            if logic_peak - equity > rollback_threshold:
                next_mode = "initial"
                waiting_recovery = True
                recovery_peak = logic_peak
                rollback_adjust_count += 1

    _flush_week_sample()

    first_date = str(cagr_start_date or "").strip()
    last_date = str(cagr_end_date or "").strip()
    if not first_date or not last_date:
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

    return {
        "initial_net_value": round(initial, 6),
        "final_net_value": round(equity, 6),
        "profit_multiple": round(multiple, 6),
        "cagr_pct": round(cagr_pct, 6),
        "mdd_pct": round(mdd_pct_max, 6),
        "mdd_amount": round(mdd_amount, 6),
        "mdd_pct_date": mdd_pct_date or "未達成",
        "mdd_amount_date": mdd_amount_date or "未達成",
        "rollback_adjust_count": int(rollback_adjust_count),
        "reach_max_multiple_date": reach_max_multiple_date or "未達成",
        "reach_10x_date": reach_10x_date or "未達成",
        "curve": curve,
    }


def build_dynamic_compounding(trades: list[dict], config: DynamicCompoundingConfig) -> dict:
    weekly_periods = _weekly_periods(trades)
    monthly_periods = _monthly_periods(trades)
    cagr_start_date = ""
    cagr_end_date = ""
    if trades:
        dates: list[datetime] = []
        for t in trades:
            ds = str(t.get("trade_date2", ""))[:10]
            if not ds:
                continue
            try:
                dates.append(_dt(ds))
            except ValueError:
                continue
        if dates:
            dates.sort()
            cagr_start_date = dates[0].strftime("%Y-%m-%d")
            cagr_end_date = dates[-1].strftime("%Y-%m-%d")
    return {
        "weekly": _simulate(
            weekly_periods,
            config,
            cagr_start_date=cagr_start_date,
            cagr_end_date=cagr_end_date,
        ),
        "monthly": _simulate(
            monthly_periods,
            config,
            cagr_start_date=cagr_start_date,
            cagr_end_date=cagr_end_date,
        ),
    }
