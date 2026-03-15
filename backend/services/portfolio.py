from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from backend.services.parser import TradeItem


def merge_trades(
    strategy_trades: list[tuple[list[TradeItem], dict]],
    start: datetime | None,
    end: datetime | None,
    factor: float = 1.0,
) -> list[dict]:
    merged: list[TradeItem] = []
    for trades, equity_cfg in strategy_trades:
        weight = float(equity_cfg.get("weight", 1.0))
        contract_mul = float(equity_cfg.get("contract", 1.0))

        for t in trades:
            scaled = TradeItem(
                idx=t.idx,
                trade_date1=t.trade_date1,
                trade_date2=t.trade_date2,
                profit=t.profit * weight * contract_mul * factor,
                net_profit=t.net_profit * weight * contract_mul * factor,
                trade_amount=t.trade_amount * contract_mul * weight * factor,
                bs=t.bs,
                contract=t.contract * contract_mul,
                price1=t.price1,
                price2=t.price2,
                point_value=t.point_value,
                strategy_index=t.strategy_index,
            )
            merged.append(scaled)

    merged.sort(key=lambda t: (t.trade_date2, t.idx))

    out: list[dict] = []
    aux_idx = 1
    for t in merged:
        if start and t.trade_date2 < start:
            continue
        if end and t.trade_date2 > end:
            continue
        item = asdict(t)
        item["trade_date1"] = t.trade_date1.strftime("%Y-%m-%d %H:%M:%S")
        item["trade_date2"] = t.trade_date2.strftime("%Y-%m-%d %H:%M:%S")
        item["aux_idx"] = aux_idx
        aux_idx += 1
        out.append(item)

    return out
