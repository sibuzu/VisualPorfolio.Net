from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from backend.services.parser import TradeItem


def _signed_contract(t: TradeItem) -> float:
    side = str(t.bs or "").upper()
    qty = float(t.contract or 0.0)
    if side == "B":
        return qty
    if side == "S":
        return -qty
    return 0.0


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

    # If a strategy already has open position at range start, skip its trades
    # until that carried position is flattened, then start counting performance.
    position_by_strategy: dict[int, float] = {}
    if start:
        for t in merged:
            if t.trade_date2 >= start:
                break
            key = int(t.strategy_index)
            position_by_strategy[key] = position_by_strategy.get(key, 0.0) + _signed_contract(t)

    warmup_strategies = {
        key for key, pos in position_by_strategy.items() if abs(float(pos)) > 1e-9
    }

    out: list[dict] = []
    aux_idx = 1
    for t in merged:
        key = int(t.strategy_index)
        if start and t.trade_date2 < start:
            continue
        position_by_strategy[key] = position_by_strategy.get(key, 0.0) + _signed_contract(t)
        if end and t.trade_date2 > end:
            continue
        if key in warmup_strategies:
            if abs(float(position_by_strategy.get(key, 0.0))) <= 1e-9:
                warmup_strategies.remove(key)
            continue
        item = asdict(t)
        item["trade_date1"] = t.trade_date1.strftime("%Y-%m-%d %H:%M:%S")
        item["trade_date2"] = t.trade_date2.strftime("%Y-%m-%d %H:%M:%S")
        item["aux_idx"] = aux_idx
        aux_idx += 1
        out.append(item)

    return out
