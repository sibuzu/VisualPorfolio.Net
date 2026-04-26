from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import io
import json
import os
from pathlib import Path
import re
from typing import Iterable, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile


FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")


class BuyHoldError(ValueError):
    pass


@dataclass(frozen=True)
class PricePoint:
    date: str
    close: float
    contract_date: str = ""


@dataclass(frozen=True)
class DividendPoint:
    date: str
    cash: float


@dataclass(frozen=True)
class BuyHoldResult:
    display_name: str
    filename: str
    payload: bytes
    quantity: float
    points: list[PricePoint]


class FinMindFetcher(Protocol):
    def stock_prices(self, code: str, start_date: str) -> list[dict]:
        ...

    def stock_dividends(self, code: str, start_date: str) -> list[dict]:
        ...

    def futures_prices(self, code: str, start_date: str) -> list[dict]:
        ...


class HttpFinMindFetcher:
    def __init__(self, token: str | None = None, timeout: float = 20.0) -> None:
        self.token = token if token is not None else os.getenv("FINMIND_TOKEN", "")
        self.timeout = timeout

    def _get(self, params: dict[str, str]) -> list[dict]:
        query = urlencode({k: v for k, v in params.items() if v != ""})
        request = Request(f"{FINMIND_URL}?{query}")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urlopen(request, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except Exception as exc:
            raise BuyHoldError(f"FinMind request failed: {exc}") from exc
        try:
            doc = json.loads(body)
        except Exception as exc:
            raise BuyHoldError("FinMind response is not valid JSON") from exc
        if doc.get("status") not in {None, 200, "200"} and not doc.get("data"):
            raise BuyHoldError(str(doc.get("msg") or doc.get("message") or "FinMind request failed"))
        data = doc.get("data")
        return data if isinstance(data, list) else []

    def stock_prices(self, code: str, start_date: str) -> list[dict]:
        return self._get({"dataset": "TaiwanStockPrice", "data_id": code, "start_date": start_date})

    def stock_dividends(self, code: str, start_date: str) -> list[dict]:
        return self._get({"dataset": "TaiwanStockDividend", "data_id": code, "start_date": start_date})

    def futures_prices(self, code: str, start_date: str) -> list[dict]:
        return self._get({"dataset": "TaiwanFuturesDaily", "data_id": code, "start_date": start_date})


def parse_positive_amount_wan(text: str) -> float:
    value = _parse_float(text)
    if value <= 0:
        raise BuyHoldError("金額(萬) must be greater than 0")
    return value


def parse_positive_leverage(text: str | None) -> float:
    value = _parse_float(text or "5")
    if value <= 0:
        raise BuyHoldError("槓桿 must be greater than 0")
    return value


def display_name_for(code: str, amount_wan_text: str) -> str:
    code_text = str(code or "").strip().upper()
    amount_text = str(amount_wan_text or "").strip()
    if not code_text:
        raise BuyHoldError("代碼 is required")
    if not amount_text:
        raise BuyHoldError("金額(萬) is required")
    return f"BH{code_text}_{amount_text}萬"


def generated_filename(display_name: str) -> str:
    stem = _SAFE_NAME_RE.sub("_", display_name).strip("._") or "BH"
    return f"{stem}.sea"


def build_buy_hold_sea(
    *,
    folder: Path,
    buy_date: str,
    amount_wan_text: str,
    product_type: str,
    code: str,
    leverage_text: str | None = None,
    fetcher: FinMindFetcher | None = None,
) -> BuyHoldResult:
    _parse_date(buy_date)
    code_text = str(code or "").strip().upper()
    display_name = display_name_for(code_text, amount_wan_text)
    filename = generated_filename(display_name)
    capital = parse_positive_amount_wan(amount_wan_text) * 10_000.0
    fetcher = fetcher or HttpFinMindFetcher()

    if product_type == "股票":
        points = normalize_stock_prices(fetcher.stock_prices(code_text, buy_date))
        dividends = normalize_stock_dividends(fetcher.stock_dividends(code_text, buy_date))
        events, quantity = build_stock_events(code_text, capital, points, dividends)
    elif product_type == "期貨":
        leverage = parse_positive_leverage(leverage_text)
        points = normalize_futures_prices(fetcher.futures_prices(code_text, buy_date))
        events, quantity = build_futures_events(code_text, capital, leverage, points)
    else:
        raise BuyHoldError("商品 must be 股票 or 期貨")

    payload = serialize_sea(
        display_name=display_name,
        code=code_text,
        product_type=product_type,
        amount_wan_text=amount_wan_text,
        leverage_text=leverage_text if product_type == "期貨" else "",
        events=events,
    )
    return BuyHoldResult(display_name=display_name, filename=filename, payload=payload, quantity=quantity, points=points)


def save_buy_hold_sea(folder: Path, result: BuyHoldResult) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / result.filename
    path.write_bytes(result.payload)
    return path


def normalize_stock_prices(rows: Iterable[dict]) -> list[PricePoint]:
    points: list[PricePoint] = []
    for row in rows:
        d = _row_date(row)
        close = _row_float(row, ("close", "Close"))
        if d and close > 0:
            points.append(PricePoint(date=d, close=close))
    points.sort(key=lambda p: p.date)
    if not points:
        raise BuyHoldError("FinMind has no usable stock price data")
    return _dedupe_by_date(points)


def normalize_stock_dividends(rows: Iterable[dict]) -> list[DividendPoint]:
    points: list[DividendPoint] = []
    for row in rows:
        d = _row_date(row, ("date", "stock_date", "CashExDividendTradingDate", "ex_dividend_date"))
        cash = _first_positive_float(
            row,
            (
                "CashEarningsDistribution",
                "cash_earnings_distribution",
                "cash_dividend",
                "stock_and_cache_dividend",
                "dividend",
            ),
        )
        if d and cash > 0:
            points.append(DividendPoint(date=d, cash=cash))
    points.sort(key=lambda p: p.date)
    return points


def normalize_futures_prices(rows: Iterable[dict]) -> list[PricePoint]:
    points: list[PricePoint] = []
    for row in rows:
        d = _row_date(row)
        close = _first_positive_float(row, ("close", "settlement_price", "Close", "SettlementPrice"))
        contract_date = str(row.get("contract_date") or row.get("ContractDate") or "")
        if d and close > 0:
            points.append(PricePoint(date=d, close=close, contract_date=contract_date))
    points.sort(key=lambda p: (p.date, _contract_sort_key(p.contract_date)))
    if not points:
        raise BuyHoldError("FinMind has no usable futures data")
    selected: dict[str, PricePoint] = {}
    for d in sorted({p.date for p in points}):
        day_points = [p for p in points if p.date == d]
        selected[d] = _select_rollover_contract(day_points)
    return [selected[d] for d in sorted(selected)]


def build_stock_events(
    code: str,
    capital: float,
    points: list[PricePoint],
    dividends: list[DividendPoint],
) -> tuple[list[dict], float]:
    if not points:
        raise BuyHoldError("FinMind has no usable stock price data")
    quantity = capital / points[0].close
    if quantity <= 0:
        raise BuyHoldError("Cannot calculate stock position")
    dividend_by_date: dict[str, float] = {}
    for div in dividends:
        dividend_by_date[div.date] = dividend_by_date.get(div.date, 0.0) + div.cash

    events = [_trade_event(points[0].date, code, points[0].close, quantity)]
    for point in points[1:]:
        cash_per_unit = dividend_by_date.get(point.date, 0.0)
        if cash_per_unit > 0:
            add_qty = (quantity * cash_per_unit) / point.close
            if add_qty > 0:
                events.append(_trade_event(point.date, code, point.close, add_qty))
                quantity += add_qty
        events.append(_price_event(point.date, code, point.close))
    events.append(_trade_event(points[-1].date, code, points[-1].close, -quantity))
    return events, quantity


def build_futures_events(
    code: str,
    capital: float,
    leverage: float,
    points: list[PricePoint],
) -> tuple[list[dict], float]:
    if not points:
        raise BuyHoldError("FinMind has no usable futures data")
    quantity = (capital * leverage) / points[0].close
    if quantity <= 0:
        raise BuyHoldError("Cannot calculate futures position")
    symbol = _futures_symbol(code, points[0])
    events = [_trade_event(points[0].date, symbol, points[0].close, quantity)]
    active_symbol = symbol
    for point in points[1:]:
        next_symbol = _futures_symbol(code, point)
        if next_symbol != active_symbol:
            events.append(_trade_event(point.date, active_symbol, point.close, -quantity))
            events.append(_trade_event(point.date, next_symbol, point.close, quantity))
            active_symbol = next_symbol
        else:
            events.append(_price_event(point.date, active_symbol, point.close))
    events.append(_trade_event(points[-1].date, active_symbol, points[-1].close, -quantity))
    return events, quantity


def serialize_sea(
    *,
    display_name: str,
    code: str,
    product_type: str,
    amount_wan_text: str,
    leverage_text: str | None,
    events: list[dict],
) -> bytes:
    archive_stem = _SAFE_NAME_RE.sub("_", display_name).strip("._") or "BH"
    strategy_toml = "\n".join(
        [
            "[strategy]",
            f'name = "{_toml_escape(display_name)}"',
            'project = "sea"',
            f'strategy_id = "{_toml_escape(display_name)}"',
            "",
            "[params]",
            '"Strategy" = "Buy&Hold"',
            f'"Symbol" = "{_toml_escape(code)}"',
            f'"商品" = "{_toml_escape(product_type)}"',
            f'"金額(萬)" = "{_toml_escape(amount_wan_text)}"',
            f'"槓桿" = "{_toml_escape(leverage_text or "")}"',
            '"交易成本" = "0"',
            '"契約價值" = "1"',
            "",
        ]
    )
    events_jsonl = "\n".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) for event in events)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{archive_stem}/strategy.toml", strategy_toml)
        zf.writestr(f"{archive_stem}/events.jsonl", events_jsonl)
    return buf.getvalue()


def _trade_event(day: str, symbol: str, price: float, quantity: float) -> dict:
    return {
        "timestamp": f"{day}T00:00:00Z",
        "type": "trade",
        "data": {"instrument_id": symbol, "price": round(float(price), 8), "quantity": float(quantity)},
    }


def _price_event(day: str, symbol: str, price: float) -> dict:
    return {
        "timestamp": f"{day}T00:00:00Z",
        "type": "price",
        "data": {"instrument_id": symbol, "price": round(float(price), 8)},
    }


def _select_rollover_contract(points: list[PricePoint]) -> PricePoint:
    if len(points) == 1:
        return points[0]
    dated = [p for p in points if p.contract_date]
    if dated:
        return sorted(dated, key=lambda p: _contract_sort_key(p.contract_date))[0]
    return points[0]


def _futures_symbol(code: str, point: PricePoint) -> str:
    suffix = point.contract_date.strip()
    return f"{code}_{suffix}" if suffix else code


def _contract_sort_key(value: str) -> tuple[int, str]:
    digits = re.sub(r"\D+", "", str(value or ""))
    if len(digits) >= 6:
        return (int(digits[:6]), str(value))
    if len(digits) >= 4:
        return (int(digits[:4]), str(value))
    return (999999, str(value))


def _parse_float(value: str | int | float | None) -> float:
    text = str(value if value is not None else "").strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return float(text)
    except ValueError as exc:
        raise BuyHoldError(f"Invalid number: {value}") from exc


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise BuyHoldError("日期 must use YYYY-MM-DD") from exc


def _row_date(row: dict, keys: tuple[str, ...] = ("date", "Date")) -> str:
    for key in keys:
        val = row.get(key)
        if val:
            text = str(val).strip()
            if len(text) >= 10:
                return text[:10].replace("/", "-")
            return text
    return ""


def _row_float(row: dict, keys: tuple[str, ...]) -> float:
    for key in keys:
        if key in row and row.get(key) not in {None, ""}:
            try:
                return float(str(row.get(key)).replace(",", ""))
            except ValueError:
                return 0.0
    return 0.0


def _first_positive_float(row: dict, keys: tuple[str, ...]) -> float:
    for key in keys:
        val = _row_float(row, (key,))
        if val > 0:
            return val
    return 0.0


def _dedupe_by_date(points: list[PricePoint]) -> list[PricePoint]:
    by_date: dict[str, PricePoint] = {}
    for point in points:
        by_date[point.date] = point
    return [by_date[d] for d in sorted(by_date)]


def _toml_escape(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"')
