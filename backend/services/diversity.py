from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _corr(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or not x:
        return 0.0
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    sxy = 0.0
    sxx = 0.0
    syy = 0.0
    for i in range(len(x)):
        dx = x[i] - mx
        dy = y[i] - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
    if sxx <= 0 or syy <= 0:
        return 0.0
    val = sxy / sqrt(sxx * syy)
    return max(-1.0, min(1.0, val))


def build_diversity(trades: list[dict]) -> dict:
    if not trades:
        return {
            "strategy_count": 0,
            "metrics": {},
            "details": [],
        }

    strat_daily: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    strat_amount = defaultdict(float)
    strat_count = defaultdict(int)
    merged_by_time = defaultdict(float)
    per_strat_by_time = defaultdict(lambda: defaultdict(float))

    for t in trades:
        si = int(t["strategy_index"])
        dt = datetime.strptime(str(t["trade_date2"]), "%Y-%m-%d %H:%M:%S")
        day = dt.strftime("%Y-%m-%d")
        ts = str(t["trade_date2"])

        profit = float(t["net_profit"])
        amt = abs(float(t["trade_amount"]))

        strat_daily[si][day] += profit
        strat_amount[si] += amt
        if amt > 0:
            strat_count[si] += 1

        merged_by_time[ts] += amt
        per_strat_by_time[ts][si] += amt

    strategies = sorted(strat_daily.keys())
    strat_n = len(strategies)
    total_amount = sum(merged_by_time.values())
    N = len(merged_by_time)
    avg_amount = (total_amount / N) if N else 0.0

    hhi = 0.0
    if total_amount > 0:
        for v in merged_by_time.values():
            s = v / total_amount
            hhi += s * s
    n_eff = (1.0 / hhi) if hhi > 0 else 0.0
    eer = (n_eff / N) if N else 0.0

    # Daily series and corr matrix
    all_days = sorted({d for m in strat_daily.values() for d in m.keys()})
    series = {si: [strat_daily[si].get(day, 0.0) for day in all_days] for si in strategies}
    corr = defaultdict(dict)
    for i in strategies:
        for j in strategies:
            corr[i][j] = 1.0 if i == j else _corr(series[i], series[j])

    weights = []
    total_raw_weight = sum(strat_amount[si] for si in strategies)
    for si in strategies:
        w = (strat_amount[si] / total_raw_weight) if total_raw_weight else 0.0
        weights.append((si, w))

    portfolio_series = []
    for day in all_days:
        portfolio_series.append(sum(strat_daily[si].get(day, 0.0) for si in strategies))
    sigma_p = _std(portfolio_series)
    sigma_weighted = sum(_std(series[si]) for si in strategies)
    rdr = (sigma_weighted / sigma_p) if sigma_p else 0.0

    dci_num = 0.0
    dci_den = 0.0
    enb_den = 0.0
    for si, wi in weights:
        enb_den += wi * wi
        for sj, wj in weights:
            if si != sj:
                pair_w = wi * wj
                dci_num += pair_w * corr[si][sj]
                dci_den += pair_w
                enb_den += pair_w * corr[si][sj]
    dci = (dci_num / dci_den) if dci_den else 1.0
    isn = (1.0 / enb_den) if enb_den > 0 else 0.0

    dsn = 0.0
    if strat_n >= 2 and total_amount > 0:
        dsn_weighted_sum = 0.0
        dsn_total_weight = 0.0
        for ts, strat_map in per_strat_by_time.items():
            w = [strat_map.get(si, 0.0) for si in strategies]
            sum_w = sum(w)
            sum_w2 = sum(x * x for x in w)
            if sum_w <= 0:
                continue
            dsn_t = strat_n * sum_w2 / (sum_w * sum_w)
            dsn_weighted_sum += dsn_t * sum_w
            dsn_total_weight += sum_w
        dsn = (dsn_weighted_sum / dsn_total_weight) if dsn_total_weight else 0.0

    details = []
    for si in sorted(strategies, key=lambda x: strat_amount[x], reverse=True):
        amount = strat_amount[si]
        avg_corr = (
            sum(corr[si][sj] for sj in strategies if sj != si) / (strat_n - 1)
            if strat_n > 1
            else 1.0
        )
        details.append(
            {
                "strategy_index": si,
                "amount_share": round((amount / total_raw_weight) if total_raw_weight else 0.0, 6),
                "trade_count": strat_count[si],
                "total_amount": round(amount, 6),
                "avg_amount": round((amount / strat_count[si]) if strat_count[si] else 0.0, 6),
                "avg_correlation": round(avg_corr, 6),
            }
        )

    return {
        "strategy_count": strat_n,
        "metrics": {
            "N": N,
            "avg_amount": round(avg_amount, 6),
            "N_eff": round(n_eff, 6),
            "EER": round(eer, 6),
            "RDR": round(rdr, 6),
            "DCI": round(dci, 6),
            "ISN": round(isn, 6),
            "DSN": round(dsn, 6),
        },
        "details": details,
    }
