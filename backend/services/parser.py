from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
import tomllib


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
    value = str(value or "").strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    fmts = [
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported datetime format: {value}")


def _pct_or_pt(price: float, ratio_or_point: str) -> float:
    # Rule:
    # - With '%' (or full-width '％'): treat as percentage of price.
    # - Without '%': treat as fixed big-point value. Final money impact is
    #   fixed_value * point_value (applied later in _records_to_trade_items).
    text = (ratio_or_point or "0").strip()
    if text.endswith("%") or text.endswith("％"):
        return price * _to_float(text[:-1], 0.0) / 100.0
    return _to_float(text, 0.0)


def parse_file(path: Path, strategy_index: int) -> list[TradeItem]:
    ext = path.suffix.lower()
    if ext in {".sea", ".gsea"}:
        if ext == ".sea":
            return _parse_sea_file(path, strategy_index)
        return _parse_gsea_file(path, strategy_index)

    root = ET.parse(path).getroot()
    if root.tag == "策略回測":
        return _parse_srp_as_net_value_series(root, strategy_index)
    if root.tag == "CryptoReport":
        return _parse_xrp_as_net_value_series(root, strategy_index)
    raise ValueError(f"Unsupported root tag: {root.tag}")


def _find_zip_text_entry(zf: zipfile.ZipFile, suffix: str) -> str:
    for name in zf.namelist():
        if name.lower().endswith(suffix.lower()):
            return zf.read(name).decode("utf-8-sig")
    return ""


def _parse_strategy_slippage(strategy_toml: str) -> str:
    def _is_zero_cost_text(value: str) -> bool:
        text = str(value or "").strip().replace("％", "%")
        if not text:
            return True
        if text.endswith("%"):
            text = text[:-1].strip()
        return abs(_to_float(text, 0.0)) < 1e-12

    if not strategy_toml:
        return "0"
    try:
        doc = tomllib.loads(strategy_toml)
        params = doc.get("params", {})
        if isinstance(params, dict):
            # Treat these keys as equivalent transaction-cost fields.
            alias_keys = ("滑價成本", "滑價", "交易成本", "TradeCost", "Slippage")

            basic = params.get("基本設定", {})
            basic_value: str | None = None
            if isinstance(basic, dict):
                for key in alias_keys:
                    raw = basic.get(key)
                    if raw is not None and str(raw).strip():
                        basic_value = str(raw)
                        break

            params_value: str | None = None
            for key in alias_keys:
                raw = params.get(key)
                if raw is not None and str(raw).strip():
                    params_value = str(raw)
                    break

            # If basic setting is explicit zero but params carries a non-zero
            # cost, prefer params-level value for backward compatibility.
            if basic_value is not None:
                if params_value is not None and _is_zero_cost_text(basic_value) and not _is_zero_cost_text(params_value):
                    return params_value
                return basic_value
            if params_value is not None:
                return params_value
    except Exception:
        pass
    return "0"


def _parse_strategy_point_value(strategy_toml: str) -> float:
    if not strategy_toml:
        return 1.0
    try:
        doc = tomllib.loads(strategy_toml)
        params = doc.get("params", {})
        if isinstance(params, dict):
            alias_keys = ("契約價值", "ContractValue", "BigPointValue")

            basic = params.get("基本設定", {})
            if isinstance(basic, dict):
                for key in alias_keys:
                    raw = basic.get(key)
                    if raw is not None and str(raw).strip():
                        return max(_to_float(str(raw), 1.0), 1e-12)

            for key in alias_keys:
                raw = params.get(key)
                if raw is not None and str(raw).strip():
                    return max(_to_float(str(raw), 1.0), 1e-12)
    except Exception:
        pass
    return 1.0


def _parse_sea_records(strategy_toml: str, events_jsonl: str) -> tuple[list[TradeRecord], str]:
    slippage = _parse_strategy_slippage(strategy_toml)
    records: list[TradeRecord] = []
    pos_by_symbol: dict[str, float] = {}

    for raw in (events_jsonl or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        event = json.loads(line)
        event_type = str(event.get("type", "")).strip().lower()
        ts = _to_dt(str(event.get("timestamp", "1970-01-01T00:00:00")))
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if not data:
            continue

        symbol = str(data.get("instrument_id", "SYM"))
        price = _to_float(str(data.get("price", 0.0)), 0.0)
        if event_type == "trade":
            qty = _to_float(str(data.get("quantity", 0.0)), 0.0)
            # price=0 is valid for option expiry/close events in legacy SRP-derived SEA.
            if qty == 0 or price < 0:
                continue
            bs = "B" if qty > 0 else "S"
            records.append(
                TradeRecord(
                    strategy_index=0,
                    bs=bs,
                    contract=abs(qty),
                    price=price,
                    time_stamp=ts,
                    trade_type="",
                    symbol=symbol,
                )
            )
            pos_by_symbol[symbol] = pos_by_symbol.get(symbol, 0.0) + qty
            continue

        if event_type == "price":
            pos = pos_by_symbol.get(symbol, 0.0)
            # price snapshots can also be 0 in some legacy datasets.
            if pos == 0 or price < 0:
                continue
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
                    trade_type="x",
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
                    trade_type="x",
                    symbol=symbol,
                )
            )

    return records, slippage


def _parse_sea_file(path: Path, strategy_index: int) -> list[TradeItem]:
    with zipfile.ZipFile(path, "r") as zf:
        strategy_toml = _find_zip_text_entry(zf, "/strategy.toml")
        events_jsonl = _find_zip_text_entry(zf, "/events.jsonl")
    if not events_jsonl:
        raise ValueError("Cannot find events.jsonl in .sea")
    records, slippage = _parse_sea_records(strategy_toml, events_jsonl)
    point_value = _parse_strategy_point_value(strategy_toml)
    return _records_to_trade_items(records, point_value=point_value, slippage=slippage, strategy_index=strategy_index)


def _parse_gsea_group_items(group_text: str) -> dict[str, float]:
    if not group_text:
        return {}
    try:
        # Tolerate trailing commas in legacy group.json files.
        cleaned = re.sub(r",(\s*[}\]])", r"\1", group_text)
        group = json.loads(cleaned).get("group", [])
    except Exception:
        return {}

    scales: dict[str, float] = {}
    for item in group:
        if not isinstance(item, dict):
            continue
        name = str(item.get("project", "")).strip()
        if not name:
            continue
        count = _to_float(str(item.get("count", 1)), 1.0)
        weight = _to_float(str(item.get("weight", 1)), 1.0)
        scales[name.lower()] = max(count, 0.0) * weight
    return scales


def _parse_gsea_file(path: Path, strategy_index: int) -> list[TradeItem]:
    all_records: list[TradeRecord] = []
    slippage = "0"
    with zipfile.ZipFile(path, "r") as zf:
        group_text = _find_zip_text_entry(zf, "/group.json")
        scales = _parse_gsea_group_items(group_text)

        sea_names = [name for name in zf.namelist() if name.lower().endswith(".sea")]
        for sea_name in sea_names:
            sea_base = Path(sea_name).stem.lower()
            scale = scales.get(sea_base, 1.0)
            if scale <= 0:
                continue
            sea_bytes = zf.read(sea_name)
            # Read embedded .sea from memory.
            with zipfile.ZipFile(io.BytesIO(sea_bytes), "r") as sea_zip:
                strategy_toml = _find_zip_text_entry(sea_zip, "/strategy.toml")
                events_jsonl = _find_zip_text_entry(sea_zip, "/events.jsonl")
            if not events_jsonl:
                continue
            sea_records, sea_slippage = _parse_sea_records(strategy_toml, events_jsonl)
            point_value = _parse_strategy_point_value(strategy_toml)
            slippage = sea_slippage or slippage
            for rec in sea_records:
                rec.contract *= (scale * point_value)
            all_records.extend(sea_records)

    if not all_records:
        raise ValueError("No valid .sea entries found in .gsea")
    return _records_to_trade_items(all_records, point_value=1.0, slippage=slippage, strategy_index=strategy_index)


def _parse_srp_as_net_value_series(root: ET.Element, strategy_index: int) -> list[TradeItem]:
    param_node = root.find("參數")
    min_point_unit = _to_float(param_node.findtext("最小跳動點") if param_node is not None else "1", 1.0)
    min_point_price = _to_float(param_node.findtext("最小跳動金額") if param_node is not None else "1", 1.0)
    point_value = min_point_price / min_point_unit if min_point_unit else 1.0
    slippage_raw = (param_node.findtext("滑價") if param_node is not None else "") or ""
    slippage = slippage_raw.strip() or "0"

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
