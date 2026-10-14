from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import PurePosixPath
import tomllib
import xml.etree.ElementTree as ET
import zipfile

from .model import ReportFormatError, ReportSource, TradeEvent


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 128
_CAPITAL_KEYS = {"initcapital", "initialcapital", "初始資金"}


def _decimal(value: object, *, default: Decimal | None = None, field: str = "number") -> Decimal:
    raw = str(value if value is not None else "").strip().replace(",", "").replace("$", "")
    if not raw:
        if default is not None:
            return default
        raise ReportFormatError(f"Missing {field}")
    multiple = Decimal(10000) if raw.endswith("萬") else Decimal(1)
    if multiple != 1:
        raw = raw[:-1].strip()
    try:
        number = Decimal(raw) * multiple
    except InvalidOperation as exc:
        raise ReportFormatError(f"Invalid {field}") from exc
    if not number.is_finite():
        raise ReportFormatError(f"Invalid {field}")
    return number


def _date(value: object) -> datetime:
    raw = str(value or "").strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    for text in (raw, raw.replace("/", "-")):
        try:
            parsed = datetime.fromisoformat(text)
            return parsed.replace(tzinfo=None)
        except ValueError:
            pass
    raise ReportFormatError("Invalid trade timestamp")


def _initial_capital(*settings: dict[str, object]) -> Decimal | None:
    for group in settings:
        for key, value in group.items():
            if key.lower() not in _CAPITAL_KEYS:
                continue
            try:
                capital = _decimal(value, field=key)
            except ReportFormatError:
                continue
            if capital > 0:
                return capital
    return None


def _point_value(params: dict[str, str]) -> Decimal:
    tick_size = _decimal(params.get("最小跳動點", params.get("MinPointUnit", "")), default=Decimal(0))
    tick_value = _decimal(params.get("最小跳動金額", params.get("MinPointPrice", "")), default=Decimal(0))
    if tick_size > 0 and tick_value > 0:
        return tick_value / tick_size
    contract_value = _decimal(params.get("契約價值", params.get("ContractValue", "")), default=Decimal(0))
    return contract_value if contract_value > 0 else Decimal(1)


def _slippage_text(params: dict[str, str]) -> str:
    text = params.get("滑價") or params.get("Slippage") or params.get("交易成本") or "0"
    raw = text.strip().replace("％", "%")
    value = _decimal(raw[:-1] if raw.endswith("%") else raw, field="slippage")
    if value < 0:
        raise ReportFormatError("Invalid slippage")
    return text


def parse_report(filename: str, content: bytes) -> ReportSource:
    if not content:
        raise ReportFormatError("Empty report")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ReportFormatError("Report exceeds 20 MiB upload limit")
    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    if suffix == ".srp":
        return _parse_srp(filename, content)
    if suffix == ".sea":
        return _parse_sea(filename, content)
    raise ReportFormatError("Only .srp and .sea reports are supported")


def _parse_srp(filename: str, content: bytes) -> ReportSource:
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ReportFormatError("XML document declarations are not allowed")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ReportFormatError("Invalid SRP XML") from exc
    if root.tag != "策略回測":
        raise ReportFormatError("SRP root must be 策略回測")
    params = {child.tag: (child.text or "").strip() for child in root.findall("./參數/*")}
    strategy_node = root.find("./策略參數")
    strategy_params: dict[str, str] = {}
    if strategy_node is not None:
        first = next(iter(strategy_node), None)
        if first is not None:
            strategy_params = {child.tag: (child.text or "").strip() for child in first}
    strategy = params.get("策略") or (next(iter(strategy_node)).tag if strategy_node is not None and len(strategy_node) else "SRP Strategy")
    symbol = params.get("近月代碼") or "TX"
    instrument_id = symbol.split(" (", 1)[0].strip() or symbol
    trade_parent = root.find("./策略交易")
    if trade_parent is None:
        raise ReportFormatError("SRP has no 策略交易 section")
    events: list[TradeEvent] = []
    for index, node in enumerate(trade_parent.findall("Trade")):
        attrs = node.attrib
        side = attrs.get("bs", "N").upper()
        if side not in {"B", "S", "N"}:
            side = "N"
        quantity = _decimal(attrs.get("contract"), default=Decimal(0), field="contract") if side in {"B", "S"} else Decimal(0)
        if quantity < 0:
            raise ReportFormatError("Trade quantity must be nonnegative")
        price = _decimal(attrs.get("price"), default=Decimal(0), field="price")
        events.append(TradeEvent(
            index=index,
            timestamp=_date(attrs.get("time_stamp")),
            side=side,
            quantity=quantity,
            price=price,
            symbol=attrs.get("symbol") or instrument_id,
            strategy_index=_strategy_index(attrs.get("index")),
            tag=attrs.get("tag", ""),
            kind=attrs.get("type", ""),
            atr=_decimal(attrs.get("atr"), default=Decimal(0), field="atr"),
        ))
    if not events:
        raise ReportFormatError("SRP has no trades")
    return ReportSource(
        source_format="srp", filename=PurePosixPath(filename.replace("\\", "/")).name,
        strategy=strategy, symbol=symbol, params=params, strategy_params=strategy_params,
        events=tuple(sorted(events, key=lambda row: (row.timestamp, row.index))),
        point_value=_point_value(params), slippage=_slippage_text(params),
        initial_capital=_initial_capital(params, strategy_params),
        period_start=params.get("開始日期", ""), period_end=params.get("結束日期", ""),
    )


def _safe_zip_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"..", "."} for part in path.parts))


def _archive_text(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [item for item in archive.infolist() if item.filename.lower().endswith(suffix) or item.filename.lower() == suffix.lstrip("/")]
    if len(matches) != 1:
        raise ReportFormatError(f"SEA must contain one {suffix.lstrip('/')}")
    try:
        return archive.read(matches[0]).decode("utf-8-sig")
    except (UnicodeDecodeError, RuntimeError, zipfile.BadZipFile) as exc:
        raise ReportFormatError(f"Cannot read {suffix.lstrip('/')}") from exc


def _parse_sea(filename: str, content: bytes) -> ReportSource:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ReportFormatError("Invalid SEA archive") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise ReportFormatError("SEA archive has too many entries")
        if any(not _safe_zip_name(item.filename) for item in infos):
            raise ReportFormatError("SEA archive contains an unsafe path")
        if sum(item.file_size for item in infos) > MAX_UNCOMPRESSED_BYTES:
            raise ReportFormatError("SEA archive is too large when unpacked")
        if any(item.flag_bits & 1 for item in infos):
            raise ReportFormatError("Encrypted SEA archives are not supported")
        strategy_text = _archive_text(archive, "/strategy.toml")
        events_text = _archive_text(archive, "/events.jsonl")
    try:
        metadata = tomllib.loads(strategy_text)
    except tomllib.TOMLDecodeError as exc:
        raise ReportFormatError("Invalid strategy.toml") from exc
    strategy_info = metadata.get("strategy", {})
    params_raw = metadata.get("params", {})
    if not isinstance(strategy_info, dict) or not isinstance(params_raw, dict):
        raise ReportFormatError("Invalid SEA metadata")
    strategy_params_raw = params_raw.get("策略參數", {})
    if not isinstance(strategy_params_raw, dict):
        strategy_params_raw = {}
    params = {str(key): str(value) for key, value in params_raw.items() if not isinstance(value, dict)}
    strategy_params = {str(key): str(value) for key, value in strategy_params_raw.items()}
    strategy = params.get("策略") or str(strategy_info.get("name") or "SEA Strategy")
    symbol = params.get("近月代碼") or params.get("Symbol") or "SEA"
    events: list[TradeEvent] = []
    for line_no, raw_line in enumerate(events_text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ReportFormatError(f"Invalid events.jsonl line {line_no}") from exc
        if not isinstance(entry, dict):
            raise ReportFormatError(f"Invalid events.jsonl line {line_no}")
        kind = entry.get("type")
        if kind not in {"trade", "price"}:
            continue
        data = entry.get("data")
        if not isinstance(data, dict):
            raise ReportFormatError(f"Invalid events.jsonl line {line_no}")
        event_symbol = str(data.get("instrument_id") or "").strip()
        if not event_symbol:
            raise ReportFormatError(f"Missing instrument_id on line {line_no}")
        quantity = _decimal(data.get("quantity"), default=Decimal(0), field="quantity") if kind == "trade" else Decimal(0)
        if kind == "trade" and quantity == 0:
            continue
        side = "B" if quantity > 0 else "S" if quantity < 0 else "N"
        metadata_row = data.get("metadata")
        tag = str(metadata_row.get("tag") or "") if isinstance(metadata_row, dict) else ""
        events.append(TradeEvent(
            index=len(events), timestamp=_date(entry.get("timestamp")), side=side,
            quantity=abs(quantity), price=_decimal(data.get("price"), default=Decimal(0), field="price"),
            symbol=event_symbol, strategy_index=_strategy_index(data.get("hedge_id")), tag=tag,
        ))
    if not events:
        raise ReportFormatError("SEA has no trade or price events")
    return ReportSource(
        source_format="sea", filename=PurePosixPath(filename.replace("\\", "/")).name,
        strategy=strategy, symbol=symbol, params=params, strategy_params=strategy_params,
        events=tuple(sorted(events, key=lambda row: (row.timestamp, row.index))),
        point_value=_point_value(params),
        slippage=_slippage_text(params),
        initial_capital=_initial_capital(params, strategy_params),
        period_start=params.get("開始日期", ""), period_end=params.get("結束日期", ""),
    )


def _strategy_index(value: object) -> int:
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return 1
