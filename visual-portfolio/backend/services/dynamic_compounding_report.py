from __future__ import annotations

from datetime import datetime, timedelta
import io
import json
import re
import zipfile


_SAFE_STEM_RE = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")


def safe_report_stem(value: str) -> str:
    return _SAFE_STEM_RE.sub("_", str(value or "")).strip("._") or "dynamic-compounding"


def serialize_dynamic_compounding_sea(
    *,
    display_name: str,
    mode: str,
    initial_capital: float,
    trades: list[dict],
) -> bytes:
    """Serialize adjusted trades as one daily-aggregated standalone SEA report.

    All source trades closed on the same day are merged into one round trip and
    the entire report uses one synthetic instrument. Prices are normalized to
    point value 1 so adjusted quantity and adjusted P&L are both preserved.
    """
    stem = safe_report_stem(display_name)
    events: list[tuple[datetime, int, dict]] = []
    daily: dict[str, dict[str, float]] = {}

    for trade in trades:
        quantity = abs(float(trade.get("adjusted_contract", 0.0) or 0.0))
        pnl = float(trade.get("adjusted_net_profit", 0.0) or 0.0)
        if quantity <= 0:
            continue
        exit_time = _parse_datetime(trade.get("trade_date2"))
        day = exit_time.strftime("%Y-%m-%d")
        row = daily.setdefault(day, {"quantity": 0.0, "pnl": 0.0})
        row["quantity"] += quantity
        row["pnl"] += pnl

    symbol = "VPDC"
    for index, day in enumerate(sorted(daily), start=1):
        row = daily[day]
        quantity = row["quantity"]
        pnl = row["pnl"]
        price_delta = pnl / quantity
        entry_price = max(abs(price_delta) + 1.0, 1.0)
        exit_price = entry_price + price_delta
        entry_time = datetime.fromisoformat(day)
        exit_time = entry_time + timedelta(seconds=1)

        events.append((entry_time, index * 2, _trade_event(entry_time, symbol, entry_price, quantity)))
        events.append((exit_time, index * 2 + 1, _trade_event(exit_time, symbol, exit_price, -quantity)))

    if daily:
        first_timestamp = datetime.fromisoformat(min(daily))
        events.append((first_timestamp, 0, _fund_event(first_timestamp, initial_capital)))

    events.sort(key=lambda item: (item[0], item[1]))
    events_jsonl = "\n".join(json.dumps(event, ensure_ascii=False) for _, _, event in events)
    strategy_toml = (
        "[strategy]\n"
        f'name = "{_toml_text(display_name)}"\n'
        'project = "dynamic-compounding"\n'
        f'strategy_id = "{_toml_text(stem)}"\n'
        "\n"
        "[params]\n"
        f'"調整週期" = "{_toml_text(mode)}"\n'
        '"契約價值" = "1"\n'
        '"交易成本" = "0"\n'
        '"報表類型" = "動態複利逐筆調整"\n'
    )

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{stem}/strategy.toml", strategy_toml)
        archive.writestr(f"{stem}/events.jsonl", events_jsonl)
    return out.getvalue()


def _parse_datetime(value: object) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def _iso_z(value: datetime) -> str:
    return value.isoformat(timespec="seconds") + "Z"


def _trade_event(timestamp: datetime, symbol: str, price: float, quantity: float) -> dict:
    return {
        "timestamp": _iso_z(timestamp),
        "type": "trade",
        "data": {
            "instrument_id": symbol,
            "price": round(price, 12),
            "quantity": round(quantity, 12),
        },
    }


def _fund_event(timestamp: datetime, initial_capital: float) -> dict:
    return {
        "timestamp": _iso_z(timestamp),
        "type": "fund",
        "data": {
            "currency": "USD",
            "amount": float(initial_capital),
        },
    }


def _toml_text(value: object) -> str:
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"')
