from __future__ import annotations

from datetime import timedelta
import io
import json
from pathlib import Path
import tempfile
import zipfile
import xml.etree.ElementTree as ET

from backend.services.parser import TradeItem, parse_file


_LEGACY_EXTS = {".srp", ".xrp", ".xml"}


def is_legacy_trade_ext(ext: str) -> bool:
    return str(ext or "").lower() in _LEGACY_EXTS


def _to_iso_z(dt) -> str:
    text = dt.isoformat()
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def _trade_items_to_events(trades: list[TradeItem], symbol: str = "LEGACY") -> str:
    lines: list[str] = []
    for t in trades:
        qty = abs(float(t.contract or 0.0))
        if qty <= 0:
            continue

        open_qty = qty if str(t.bs or "B").upper() == "B" else -qty
        close_qty = -open_qty

        ts1 = t.trade_date1
        ts2 = t.trade_date2
        if ts2 < ts1:
            ts2 = ts1 + timedelta(seconds=1)

        open_event = {
            "timestamp": _to_iso_z(ts1),
            "type": "trade",
            "data": {
                "instrument_id": symbol,
                "price": float(t.price1 or 0.0),
                "quantity": float(open_qty),
            },
        }
        close_event = {
            "timestamp": _to_iso_z(ts2),
            "type": "trade",
            "data": {
                "instrument_id": symbol,
                "price": float(t.price2 or 0.0),
                "quantity": float(close_qty),
            },
        }
        lines.append(json.dumps(open_event, ensure_ascii=False))
        lines.append(json.dumps(close_event, ensure_ascii=False))
    return "\n".join(lines)


def _as_text(value, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or str(default)


def _to_iso_date(text: str) -> str:
    s = _as_text(text)
    if not s:
        return ""
    s = s.replace("/", "-")
    if "T" in s:
        s = s.split("T", 1)[0]
    if " " in s:
        s = s.split(" ", 1)[0]
    parts = s.split("-")
    if len(parts) == 3:
        y, m, d = parts
        if len(y) == 4 and m.isdigit() and d.isdigit():
            return f"{y}-{int(m):02d}-{int(d):02d}"
    return s


def _safe_toml_value(value: str) -> str:
    return _as_text(value).replace("\\", "\\\\").replace('"', '\\"')


def _display_text(value: str) -> str:
    text = _as_text(value)
    low = text.lower()
    if low == "true":
        return "True"
    if low == "false":
        return "False"
    return text


def _find_trade_date_range(root: ET.Element) -> tuple[str, str]:
    vals: list[str] = []
    for node in root.findall(".//Trades/Trade"):
        ts = node.attrib.get("time_stamp", "")
        iso = _to_iso_date(ts)
        if iso:
            vals.append(iso)
    if not vals:
        return "", ""
    vals.sort()
    return vals[0], vals[-1]


def _build_strategy_toml_xrp(root: ET.Element, stem: str) -> str:
    setting = root.find("./Setting")
    stg_name = _as_text(setting.findtext("Strategy") if setting is not None else "", stem)
    symbol = _as_text(setting.findtext("Symbol") if setting is not None else "", "")
    init_capital = _as_text(setting.findtext("InitCapital") if setting is not None else "", "10000")

    strategy_root = root.find("./Strategy")
    strategy_node = list(strategy_root)[0] if strategy_root is not None and list(strategy_root) else None

    fee_100 = _as_text(strategy_node.findtext("交易成本") if strategy_node is not None else "", "0.05")
    contract_value = _as_text(strategy_node.findtext("槓桿倍數") if strategy_node is not None else "", "1")
    entry_hour = _as_text(strategy_node.findtext("進場小時") if strategy_node is not None else "", "0")
    init_capital_k = _as_text(strategy_node.findtext("初始資金") if strategy_node is not None else "", "10")
    basket = _as_text(strategy_node.findtext("虛擬幣組合") if strategy_node is not None else "", "")

    start_date, end_date = _find_trade_date_range(root)
    fee_pct = f"{fee_100}%" if not fee_100.endswith("%") else fee_100

    # Keep key ordering stable for downstream tools.
    return (
        "[strategy]\n"
        f'name = "{_safe_toml_value(stg_name)}"\n'
        'project = "srp"\n'
        f'strategy_id = "{_safe_toml_value(stg_name)}"\n'
        "\n"
        "[params]\n"
        f'"Strategy" = "{_safe_toml_value(stg_name)}"\n'
        f'"Symbol" = "{_safe_toml_value(symbol)}"\n'
        f'"開始日期" = "{_safe_toml_value(start_date)}"\n'
        f'"結束日期" = "{_safe_toml_value(end_date)}"\n'
        f'"初始資金" = "{_safe_toml_value(init_capital)}"\n'
        f'"契約價值" = "{_safe_toml_value(contract_value)}"\n'
        f'"交易成本" = "{_safe_toml_value(fee_pct)}"\n'
        "\n"
        '[params."策略參數"]\n'
        f'"虛擬幣組合" = "{_safe_toml_value(basket)}"\n'
        f'"策略名稱" = "{_safe_toml_value(stg_name)}"\n'
        '"策略版本" = "v21.10.11"\n'
        f'"_交易成本100" = "{_safe_toml_value(fee_100)}"\n'
        f'"進場小時" = "{_safe_toml_value(entry_hour)}"\n'
        f'"初始資金K" = "{_safe_toml_value(init_capital_k)}"\n'
    )


def _build_strategy_toml_srp(root: ET.Element, stem: str) -> str:
    stg_parent = root.find("./策略參數")
    strategy_node = list(stg_parent)[0] if stg_parent is not None and list(stg_parent) else None
    strategy_id = strategy_node.tag if strategy_node is not None else stem
    params_node = root.find("./參數")
    pvals: dict[str, str] = {}
    if params_node is not None:
        for node in list(params_node):
            pvals[node.tag] = _display_text(node.text or "")

    strategy_short = _as_text(pvals.get("策略"), strategy_id[3:] if strategy_id.startswith("Stg") else strategy_id)
    near_month = _as_text(pvals.get("近月代碼"), "")
    symbol = near_month.split(" ", 1)[0] if near_month else ""
    start_date = _to_iso_date(_as_text(pvals.get("開始日期"), ""))
    end_date = _to_iso_date(_as_text(pvals.get("結束日期"), ""))
    fee_pct = _as_text(pvals.get("滑價"), "0.05%")
    contract_value = _as_text(pvals.get("契約價值"), "1")
    min_tick = _as_text(pvals.get("最小跳動點"), "1")

    lines: list[str] = [
        "[strategy]",
        f'name = "{_safe_toml_value(strategy_id)}"',
        'project = "srp"',
        f'strategy_id = "{_safe_toml_value(strategy_id)}"',
        "",
        "[params]",
        f'"Strategy" = "{_safe_toml_value(strategy_short)}"',
        f'"Symbol" = "{_safe_toml_value(symbol)}"',
        f'"近月代碼" = "{_safe_toml_value(near_month)}"',
        f'"契約價值" = "{_safe_toml_value(contract_value)}"',
        f'"最小跳動點" = "{_safe_toml_value(min_tick)}"',
        '"貨幣" = "USD"',
        f'"開始日期" = "{_safe_toml_value(start_date)}"',
        f'"結束日期" = "{_safe_toml_value(end_date)}"',
        f'"滑價" = "{_safe_toml_value(fee_pct)}"',
        "",
        '[params."策略參數"]',
        f'"策略名稱" = "{_safe_toml_value(strategy_short)}"',
    ]

    if strategy_node is not None:
        seen = {"策略名稱"}
        for node in list(strategy_node):
            key = node.tag
            val = _display_text(node.text or "")
            if key in seen:
                continue
            lines.append(f'"{_safe_toml_value(key)}" = "{_safe_toml_value(val)}"')
            seen.add(key)

    # Compatibility fields used by old SRP workflows.
    if strategy_node is not None and strategy_node.findtext("策略版本") is None:
        lines.append('"策略版本" = "v17.08.10"')
    if near_month:
        lines.append(f'"策略商品" = "{_safe_toml_value(near_month)}"')
    if min_tick:
        lines.append(f'"最小升降單位" = "{_safe_toml_value(min_tick)}"')
    if "有加碼" not in "".join(lines):
        lines.append('"有加碼" = "False"')
    if "星期加碼" not in "".join(lines):
        lines.append('"星期加碼" = "False"')
    if "價差加碼" not in "".join(lines):
        lines.append('"價差加碼" = "False"')

    return "\n".join(lines) + "\n"


def _build_strategy_toml_from_legacy(payload: bytes, ext: str, stem: str) -> str:
    if ext not in _LEGACY_EXTS:
        return '[params."基本設定"]\n"滑價成本" = "0"\n'
    try:
        root = ET.fromstring(payload.decode("utf-8-sig"))
    except Exception:
        return '[params."基本設定"]\n"滑價成本" = "0"\n'

    if root.tag == "CryptoReport":
        return _build_strategy_toml_xrp(root, stem)
    if root.tag == "策略回測":
        return _build_strategy_toml_srp(root, stem)
    return '[params."基本設定"]\n"滑價成本" = "0"\n'


def convert_legacy_payload_to_sea(filename: str, payload: bytes) -> tuple[str, bytes]:
    ext = Path(filename).suffix.lower()
    if ext not in _LEGACY_EXTS:
        return filename, payload

    stem = Path(filename).stem or "strategy"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(payload)
    try:
        trades = parse_file(tmp_path, strategy_index=0)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not trades:
        raise ValueError("No trades found in source file")

    events_jsonl = _trade_items_to_events(trades)
    if not events_jsonl.strip():
        raise ValueError("Cannot convert to .sea: empty events")

    strategy_toml = _build_strategy_toml_from_legacy(payload, ext, stem)
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{stem}/strategy.toml", strategy_toml)
        zf.writestr(f"{stem}/events.jsonl", events_jsonl)
        zf.writestr(f"{stem}/legacy{ext}", payload)
    return f"{stem}.sea", out_buf.getvalue()


def convert_legacy_files_in_dir(folder: Path) -> None:
    if not folder.exists():
        return
    for src in list(folder.rglob("*")):
        if not src.is_file():
            continue
        ext = src.suffix.lower()
        if ext not in _LEGACY_EXTS:
            continue
        try:
            out_name, out_payload = convert_legacy_payload_to_sea(src.name, src.read_bytes())
        except Exception:
            # Keep original file if conversion fails.
            continue
        dst = src.with_name(out_name)
        dst.write_bytes(out_payload)
        src.unlink(missing_ok=True)
