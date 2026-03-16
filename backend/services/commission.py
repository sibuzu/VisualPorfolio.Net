from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CommissionCfg:
    ref_capital: float = 840.0
    init_capital: float = 840.0
    leverage: float = 3.0
    fee_rate: float = 0.05
    rebate_rate: float = 50.0
    quarter_share_rate: float = 30.0
    bonus_thresholds: tuple[float, float, float, float] = (100.0, 150.0, 200.0, 0.0)
    bonus_rates: tuple[float, float, float, float] = (10.0, 20.0, 30.0, 0.0)


def _week_start(dt: datetime) -> datetime:
    days_to_subtract = (dt.weekday() + 1) % 7
    return dt - timedelta(days=days_to_subtract)


def _year_bonus_rate(cfg: CommissionCfg, perf: float) -> float:
    pct = perf * 100.0
    th = cfg.bonus_thresholds
    rt = cfg.bonus_rates
    if th[3] > 0 and pct >= th[3]:
        return rt[3] * 0.01
    if th[2] > 0 and pct >= th[2]:
        return rt[2] * 0.01
    if th[1] > 0 and pct >= th[1]:
        return rt[1] * 0.01
    if th[0] > 0 and pct >= th[0]:
        return rt[0] * 0.01
    return 0.0


def build_commission(trades: list[dict], rate_per_trade: float = 0.0, cfg: CommissionCfg | None = None) -> dict:
    cfg = cfg or CommissionCfg()
    cfg_payload = {
        "ref_capital": cfg.ref_capital,
        "init_capital": cfg.init_capital,
        "leverage": cfg.leverage,
        "fee_rate": cfg.fee_rate,
        "rebate_rate": cfg.rebate_rate,
        "quarter_share_rate": cfg.quarter_share_rate,
        "bonus_threshold1": cfg.bonus_thresholds[0],
        "bonus_rate1": cfg.bonus_rates[0],
        "bonus_threshold2": cfg.bonus_thresholds[1],
        "bonus_rate2": cfg.bonus_rates[1],
        "bonus_threshold3": cfg.bonus_thresholds[2],
        "bonus_rate3": cfg.bonus_rates[2],
        "bonus_threshold4": cfg.bonus_thresholds[3],
        "bonus_rate4": cfg.bonus_rates[3],
    }
    if not trades:
        return {
            "config": cfg_payload,
            "rate_per_trade": rate_per_trade,
            "trade_count": 0,
            "total_commission": 0.0,
            "net_after_commission": 0.0,
            "years": [],
        }

    trade_count = len(trades)
    simple_total = round(trade_count * rate_per_trade, 6)
    net = round(sum(float(t["net_profit"]) for t in trades) - simple_total, 6)

    rows = []
    by_year: dict[int, list[dict]] = defaultdict(list)
    for t in trades:
        dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
        by_year[dt.year].append(t)

    carry_profit = 0.0
    for year in sorted(by_year.keys()):
        cap = cfg.init_capital
        quarters = defaultdict(list)
        for t in by_year[year]:
            dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
            q = (dt.month + 2) // 3
            quarters[q].append(t)

        q_entries = []
        for q in sorted(quarters.keys()):
            qlist = quarters[q]
            week_groups: dict[datetime, list[dict]] = defaultdict(list)
            for t in qlist:
                dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
                week_groups[_week_start(dt)] += [t]

            cap_d = cap
            total_vol = 0.0
            for wk in sorted(week_groups.keys()):
                wlist = week_groups[wk]
                profit = sum(float(x["net_profit"]) for x in wlist)
                vol = sum(abs(float(x["trade_amount"])) for x in wlist)
                r = cap_d * cfg.leverage / cfg.ref_capital if cfg.ref_capital else 0.0
                cap_d += r * profit / 10000.0
                total_vol += r * vol / 10000.0

            q_start = cap
            cap = cap_d
            q_profit = cap - q_start
            carry_profit += q_profit
            share = 0.0
            if carry_profit > 0:
                share = carry_profit * cfg.quarter_share_rate * 0.01
                carry_profit = 0.0

            rebate = total_vol * cfg.fee_rate * cfg.rebate_rate * 0.0001
            q_entries.append(
                {
                    "quarter": q,
                    "start_capital": round(q_start, 6),
                    "end_capital": round(cap, 6),
                    "profit": round(q_profit, 6),
                    "share": round(share, 6),
                    "client_net_profit": round(q_profit - share, 6),
                    "rebate": round(rebate, 6),
                }
            )

        if q_entries:
            full = {
                "quarter": "全年",
                "start_capital": q_entries[0]["start_capital"],
                "end_capital": q_entries[-1]["end_capital"],
                "profit": round(q_entries[-1]["end_capital"] - q_entries[0]["start_capital"], 6),
                "share": round(sum(x["share"] for x in q_entries), 6),
                "client_net_profit": round(sum(x["client_net_profit"] for x in q_entries), 6),
                "rebate": round(sum(x["rebate"] for x in q_entries), 6),
            }
            year_perf = _safe_div(full["client_net_profit"], full["start_capital"])
            bonus_rate = _year_bonus_rate(cfg, year_perf)
            bonus = full["client_net_profit"] * bonus_rate
            rows.append(
                {
                    "year": year,
                    "entries": q_entries + [full],
                    "year_perf": round(year_perf, 6),
                    "bonus_rate": round(bonus_rate, 6),
                    "bonus": round(bonus, 6),
                    "total_income": round(bonus + full["rebate"] + full["share"], 6),
                }
            )

    return {
        "config": cfg_payload,
        "rate_per_trade": rate_per_trade,
        "trade_count": trade_count,
        "total_commission": simple_total,
        "net_after_commission": net,
        "years": rows,
    }


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0
