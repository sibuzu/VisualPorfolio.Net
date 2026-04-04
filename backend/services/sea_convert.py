from __future__ import annotations

from datetime import timedelta
import io
import json
from pathlib import Path
import tempfile
import zipfile

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

    strategy_toml = '[params."基本設定"]\n"滑價成本" = "0"\n'
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
