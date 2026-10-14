from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PeriodRec:
    wins: int = 0
    losses: int = 0
    total_win: float = 0.0
    total_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0


def _period_key(dt: datetime, period: str) -> tuple:
    if period == "day":
        return (dt.year, dt.month, dt.day)
    if period == "week":
        sunday = dt.date() - timedelta(days=(dt.weekday() + 1) % 7)
        return (sunday.year, sunday.month, sunday.day)
    if period == "month":
        return (dt.year, dt.month)
    return (dt.year,)


def _finalize(bucket_profit: float, rec: PeriodRec) -> None:
    if bucket_profit > 0:
        rec.wins += 1
        rec.total_win += bucket_profit
        rec.max_win = max(rec.max_win, bucket_profit)
    else:
        rec.losses += 1
        loss = abs(bucket_profit)
        rec.total_loss += loss
        rec.max_loss = max(rec.max_loss, loss)


def _rollup(trades: list[dict], period: str) -> PeriodRec:
    rec = PeriodRec()
    if not trades:
        return rec

    last_key = None
    bucket_profit = 0.0
    for t in trades:
        dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
        key = _period_key(dt, period)
        p = float(t["net_profit"])
        if last_key is None:
            last_key = key
            bucket_profit = p
            continue
        if key == last_key:
            bucket_profit += p
        else:
            _finalize(bucket_profit, rec)
            last_key = key
            bucket_profit = p
    _finalize(bucket_profit, rec)
    return rec


def _to_dict(rec: PeriodRec) -> dict:
    total_count = rec.wins + rec.losses
    avg_win = rec.total_win / rec.wins if rec.wins else 0.0
    avg_loss = rec.total_loss / rec.losses if rec.losses else 0.0
    return {
        "wins": rec.wins,
        "losses": rec.losses,
        "total": total_count,
        "win_prob": (rec.wins / total_count) if total_count else 0.0,
        "total_win": round(rec.total_win, 6),
        "total_loss": round(rec.total_loss, 6),
        "max_win": round(rec.max_win, 6),
        "max_loss": round(rec.max_loss, 6),
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "avg_win_loss_ratio": round((avg_win / avg_loss) if avg_loss else 1.0, 6),
        "total_win_loss_ratio": round((rec.total_win / rec.total_loss) if rec.total_loss else 1.0, 6),
    }


def build_win_loss(trades: list[dict]) -> dict:
    return {
        "day": _to_dict(_rollup(trades, "day")),
        "week": _to_dict(_rollup(trades, "week")),
        "month": _to_dict(_rollup(trades, "month")),
        "year": _to_dict(_rollup(trades, "year")),
    }
