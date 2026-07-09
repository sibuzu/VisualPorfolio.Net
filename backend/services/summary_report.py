from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _std(values: list[float]) -> float:
    if len(values) == 0:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    return sqrt(var)


def _get_year_month(dt: datetime, minterval: int) -> int:
    year = dt.year
    month0 = dt.month - 1
    return year * 100 + (month0 // minterval) * minterval + 1


def _calc_year_month_profit(
    trades: list[dict], minterval: int
) -> tuple[list[int], list[int], list[float], list[float], list[float], list[float]]:
    years: list[int] = []
    months: list[int] = []
    year_profits: list[float] = []
    month_profits: list[float] = []
    year_mdd: list[float] = []
    month_mdd: list[float] = []

    cur_year = 0
    cur_month = 0
    year_dd = 0.0
    month_dd = 0.0

    for t in trades:
        dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
        profit = float(t["net_profit"])

        ym = _get_year_month(dt, minterval)
        if ym == cur_year:
            year_profits[-1] += profit
            year_dd -= profit
            if year_dd < 0:
                year_dd = 0
            if year_dd > year_mdd[-1]:
                year_mdd[-1] = year_dd
        else:
            cur_year = ym
            years.append(cur_year)
            year_profits.append(profit)
            year_dd = max(-profit, 0.0)
            year_mdd.append(year_dd)

        ym = _get_year_month(dt, 1)
        if ym == cur_month:
            month_profits[-1] += profit
            month_dd -= profit
            if month_dd < 0:
                month_dd = 0
            if month_dd > month_mdd[-1]:
                month_mdd[-1] = month_dd
        else:
            cur_month = ym
            months.append(cur_month)
            month_profits.append(profit)
            month_dd = max(-profit, 0.0)
            month_mdd.append(month_dd)

    return years, months, year_profits, month_profits, year_mdd, month_mdd


def _calc_daily_mdds(trades: list[dict]) -> list[dict]:
    if not trades:
        return []

    daily_equity: list[float] = []
    daily_index: list[int] = []
    last_date = ""
    acc_profit = 0.0

    for i, t in enumerate(trades):
        acc_profit += float(t["net_profit"])
        trade_date = str(t["trade_date2"])[:10]
        if daily_equity and trade_date == last_date:
            daily_equity[-1] = acc_profit
            daily_index[-1] = i
        else:
            daily_equity.append(acc_profit)
            daily_index.append(i)
            last_date = trade_date

    peak = daily_equity[0]
    start_candidate = 0
    current_mdd = {"value": 0.0, "start_idx": 0, "end_idx": 0, "end_idx2": 0}
    result: list[dict] = []

    for i, equity in enumerate(daily_equity):
        drawdown = equity - peak
        if drawdown >= 0:
            peak = equity
            start_candidate = i
            if current_mdd["value"] < 0:
                current_mdd["end_idx2"] = daily_index[max(0, i - 1)]
                result.append(current_mdd.copy())
                current_mdd = {"value": 0.0, "start_idx": 0, "end_idx": 0, "end_idx2": 0}
        elif drawdown < current_mdd["value"]:
            current_mdd["value"] = drawdown
            current_mdd["start_idx"] = daily_index[start_candidate]
            current_mdd["end_idx"] = daily_index[i]

    if current_mdd["value"] < 0:
        current_mdd["end_idx2"] = daily_index[-1]
        result.append(current_mdd.copy())

    return sorted(result, key=lambda x: x["value"])


def build_report(
    trades: list[dict],
    risk_free_rate: float = 0.0,
    mdd_count: int = 5,
    capital: float = 1_000_000.0,
) -> dict:
    if not trades:
        return {
            "summary": {
                "period": "N/A",
                "trade_count": 0,
                "net_profit": 0.0,
                "mdd": 0.0,
                "profit_factor": 0.0,
                "win_prob": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "sqn": 0.0,
            },
            "equity_curve": [],
            "monthly": [],
            "annual": [],
            "weekly": [],
            "mdd_markers": [],
        }

    profits = [float(t["net_profit"]) for t in trades]
    total = sum(profits)
    real_trade_count = sum(1 for t in trades if abs(float(t.get("trade_amount", 0.0))) > 0)

    equity = 0.0
    drawdown = 0.0
    equity_curve = []

    for t in trades:
        p = float(t["net_profit"])
        equity += p
        drawdown += p
        if drawdown >= 0:
            drawdown = 0

        equity_curve.append(
            {
                "date": str(t["trade_date2"])[:10],
                "profit": round(equity, 6),
                "drawdown": round(drawdown, 6),
            }
        )

    winners = [p for p in profits if p > 0]
    losers = [p for p in profits if p < 0]
    win_prob = _safe_div(len(winners), len(profits))

    gross_profit = sum(winners)
    gross_loss_abs = abs(sum(losers))

    mean = _safe_div(total, len(profits))
    std = _std(profits)
    sqn = _safe_div(mean, std) * sqrt(len(profits)) if std > 0 else 0.0

    # Match C# daily Sharpe/Sortino approach.
    t1 = datetime.strptime(str(trades[0]["trade_date2"])[:10], "%Y-%m-%d")
    t2 = datetime.strptime(str(trades[-1]["trade_date2"])[:10], "%Y-%m-%d")
    years = max(((t2 - t1).days + 1) / 365.25, 1e-9)
    by_day: dict[str, float] = defaultdict(float)
    for t in trades:
        by_day[str(t["trade_date2"])[:10]] += float(t["net_profit"])

    ep = list(by_day.values())
    n = len(ep) / years if years > 0 else len(ep)
    rf = (risk_free_rate * 0.01) / n if n > 0 else 0.0
    used_capital = float(capital) if float(capital) > 0 else 1_000_000.0
    ep_adj = [(x / used_capital) - rf for x in ep]
    ep_mean = sum(ep_adj) / len(ep_adj) if ep_adj else 0.0
    ep_std = _std(ep_adj)
    sharpe = (sqrt(n) * ep_mean / ep_std) if ep_std > 0 and n > 0 else 0.0
    downside = [x for x in ep_adj if x < 0]
    downside_std = sqrt(sum(x * x for x in downside) / len(downside)) if downside else 0.0
    sortino = (sqrt(n) * ep_mean / downside_std) if downside_std > 0 and n > 0 else 0.0

    years, months, year_profits, month_profits, year_mdd, month_mdd = _calc_year_month_profit(
        trades, 12
    )
    annual_rows = []
    for i in range(len(years)):
        annual_rows.append(
            {
                "period": str(years[i] // 100),
                "profit": round(year_profits[i], 6),
                "mdd": round(year_mdd[i], 6),
            }
        )

    monthly_rows = []
    for i in range(len(months)):
        y = months[i] // 100
        m = months[i] % 100
        monthly_rows.append(
            {
                "period": f"{y}/{m:02d}",
                "profit": round(month_profits[i], 6),
                "mdd": round(month_mdd[i], 6),
            }
        )

    # Weekly (same Sunday anchor semantics as WinForm IsSameWeek baseline style).
    weeks: list[str] = []
    week_profit: list[float] = []
    cur_week = None
    for t in trades:
        dt = datetime.strptime(str(t["trade_date2"])[:10], "%Y-%m-%d")
        sunday = dt.date().toordinal() - ((dt.weekday() + 1) % 7)
        key = sunday
        if key == cur_week:
            week_profit[-1] += float(t["net_profit"])
        else:
            cur_week = key
            ds = datetime.fromordinal(sunday)
            weeks.append(ds.strftime("%Y/%m/%d"))
            week_profit.append(float(t["net_profit"]))
    weekly_rows = []
    total_week = 0.0
    for i in range(len(weeks)):
        total_week += week_profit[i]
        weekly_rows.append(
            {
                "period": weeks[i],
                "profit": round(week_profit[i], 6),
                "cumulative": round(total_week, 6),
            }
        )

    daily_mdds = _calc_daily_mdds(trades)
    max_dd = daily_mdds[0]["value"] if daily_mdds else 0.0

    summary = {
        "period": f"{trades[0]['trade_date2'][:10]} ~ {trades[-1]['trade_date2'][:10]}" if trades else "N/A",
        "trade_count": real_trade_count,
        "net_profit": round(total, 6),
        "mdd": round(abs(max_dd), 6),
        "profit_factor": round(_safe_div(gross_profit, gross_loss_abs), 6),
        "win_prob": round(win_prob, 6),
        "avg_win": round(_safe_div(gross_profit, len(winners)), 6),
        "avg_loss": round(_safe_div(sum(losers), len(losers)), 6),
        "sharpe": round(sharpe, 6),
        "sortino": round(sortino, 6),
        "sqn": round(sqn, 6),
    }

    mdd_markers = daily_mdds[:mdd_count]
    mdd_markers = [
        {"start_idx": x["start_idx"], "end_idx": x["end_idx"], "value": round(x["value"], 6), "end_idx2": x["end_idx2"]}
        for x in mdd_markers
    ]

    return {
        "summary": summary,
        "equity_curve": equity_curve,
        "monthly": monthly_rows,
        "annual": annual_rows,
        "weekly": weekly_rows,
        "mdd_markers": mdd_markers,
    }
