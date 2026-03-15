from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class TradeItem:
    idx: int
    trade_date1: datetime
    trade_date2: datetime
    profit: float
    net_profit: float
    trade_amount: float
    bs: str
    contract: float
    price1: float
    price2: float
    point_value: float
    strategy_index: int


@dataclass
class TradeRecord:
    strategy_index: int
    bs: str
    contract: float
    price: float
    time_stamp: datetime
    trade_type: str
    symbol: str


def _to_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    v = value.replace(",", "").replace("%", "").strip()
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _to_dt(value: str) -> datetime:
    fmts = ["%Y/%m/%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
    for fmt in fmts:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported datetime format: {value}")


def _pct_or_pt(price: float, ratio_or_point: str) -> float:
    text = (ratio_or_point or "0").strip()
    if text.endswith("%"):
        return price * _to_float(text[:-1], 0.0) / 100.0
    return _to_float(text, 0.0)


def parse_file(path: Path, strategy_index: int) -> list[TradeItem]:
    root = ET.parse(path).getroot()
    if root.tag == "策略回測":
        return _parse_srp_as_net_value_series(root, strategy_index)
    if root.tag == "CryptoReport":
        return _parse_xrp_as_net_value_series(root, strategy_index)
    raise ValueError(f"Unsupported root tag: {root.tag}")


def _parse_srp_as_net_value_series(root: ET.Element, strategy_index: int) -> list[TradeItem]:
    param_node = root.find("參數")
    min_point_unit = _to_float(param_node.findtext("最小跳動點") if param_node is not None else "1", 1.0)
    min_point_price = _to_float(param_node.findtext("最小跳動金額") if param_node is not None else "1", 1.0)
    point_value = min_point_price / min_point_unit if min_point_unit else 1.0
    slippage = (param_node.findtext("滑價") if param_node is not None else "0") or "0"

    records: list[TradeRecord] = []
    for node in root.findall("./策略交易/Trade"):
        records.append(
            TradeRecord(
                strategy_index=int(_to_float(node.attrib.get("index"), 0)),
                bs=node.attrib.get("bs", "N"),
                contract=_to_float(node.attrib.get("contract"), 0.0),
                price=_to_float(node.attrib.get("price"), 0.0),
                time_stamp=_to_dt(node.attrib.get("time_stamp", "1970/01/01 00:00:00")),
                trade_type=node.attrib.get("type", ""),
                symbol=node.attrib.get("symbol", "SYM"),
            )
        )

    return _records_to_trade_items(records, point_value, slippage, strategy_index)


def _parse_xrp_as_net_value_series(root: ET.Element, strategy_index: int) -> list[TradeItem]:
    records: list[TradeRecord] = []
    pos = 0.0
    qty = 0.0

    for node in root.findall("./Trades/Trade"):
        bs = node.attrib.get("bs", "N")
        ts = _to_dt(node.attrib.get("time_stamp", "1970/01/01"))
        symbol = node.attrib.get("symbol", "SYM")

        if bs in {"B", "S"}:
            if "amount" not in node.attrib or "qty" not in node.attrib:
                continue
            amount = _to_float(node.attrib.get("amount"), 0.0)
            qty = _to_float(node.attrib.get("qty"), 0.0)
            if qty == 0:
                continue

            rec = TradeRecord(
                strategy_index=0,
                bs=bs,
                contract=abs(qty),
                price=abs(amount / qty),
                time_stamp=ts,
                trade_type="",
                symbol=symbol,
            )
            pos += qty if bs == "B" else -qty
            records.append(rec)
        elif bs == "N" and pos != 0:
            price = _to_float(node.attrib.get("price"), 0.0)
            close_bs = "S" if pos > 0 else "B"
            open_bs = "B" if pos > 0 else "S"
            contract = abs(pos)
            records.append(
                TradeRecord(
                    strategy_index=0,
                    bs=close_bs,
                    contract=contract,
                    price=price,
                    time_stamp=ts,
                    trade_type="",
                    symbol=symbol,
                )
            )
            records.append(
                TradeRecord(
                    strategy_index=0,
                    bs=open_bs,
                    contract=contract,
                    price=price,
                    time_stamp=ts,
                    trade_type="",
                    symbol=symbol,
                )
            )

    return _records_to_trade_items(records, point_value=1.0, slippage="0", strategy_index=strategy_index)


def _records_to_trade_items(
    records: list[TradeRecord],
    point_value: float,
    slippage: str,
    strategy_index: int,
) -> list[TradeItem]:
    items: list[TradeItem] = []
    if not records:
        return items

    cash = 0.0
    net_val = 0.0
    idx = 0
    last_item: TradeItem | None = None
    qty_price_by_symbol: dict[str, dict[str, float]] = {}

    for record in records:
        qty_change = record.contract * (1.0 if record.bs == "B" else -1.0)
        book = qty_price_by_symbol.get(record.symbol, {"qty": 0.0, "price": record.price})
        book["qty"] += qty_change
        book["price"] = record.price
        qty_price_by_symbol[record.symbol] = book

        trade_amount = 0.0 if record.trade_type == "x" else record.contract * record.price * point_value
        slip = 0.0 if record.trade_type == "x" else _pct_or_pt(record.price, slippage)

        if record.bs == "B":
            cash -= record.contract * (record.price + slip) * point_value
        elif record.bs == "S":
            cash += record.contract * (record.price - slip) * point_value

        new_net_val = cash + sum(v["price"] * v["qty"] * point_value for v in qty_price_by_symbol.values())
        delta = new_net_val - net_val

        merged = False
        if last_item is not None:
            dhour = abs((record.time_stamp - last_item.trade_date1).total_seconds()) / 3600.0
            if dhour < 0.5:
                last_item.profit += delta
                last_item.net_profit = last_item.profit
                last_item.trade_amount += trade_amount
                merged = True

        if not merged:
            idx += 1
            item = TradeItem(
                idx=idx,
                trade_date1=record.time_stamp,
                trade_date2=record.time_stamp,
                profit=delta,
                net_profit=delta,
                trade_amount=trade_amount,
                bs=record.bs,
                contract=record.contract,
                price1=record.price,
                price2=record.price,
                point_value=point_value,
                strategy_index=strategy_index,
            )
            items.append(item)
            last_item = item

        net_val = new_net_val

    return items


def parse_multiple(files: list[tuple[Path, int]]) -> list[TradeItem]:
    all_items: list[TradeItem] = []
    for path, strategy_index in files:
        all_items.extend(parse_file(path, strategy_index))
    return all_items
