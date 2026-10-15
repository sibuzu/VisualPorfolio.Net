"""Independent Buy&Hold reference; strategy position sizing never enters this calculation."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import os
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .model import ReportSource


class BuyHoldSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")

    product_type: Literal["股票", "期貨"] = "股票"
    code: str = Field(default="0050", pattern=r"^[A-Z0-9._-]{1,32}$")
    amount_wan: Decimal = Field(default=Decimal(100), gt=0, le=1_000_000_000)
    leverage: Decimal = Field(default=Decimal(5), gt=0, le=100)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @property
    def name(self) -> str:
        amount = format(self.amount_wan.normalize(), "f")
        suffix = f"_{format(self.leverage.normalize(), 'f')}X" if self.product_type == "期貨" else ""
        return f"BH{self.code}_{amount}萬{suffix}"


class BuyHoldError(ValueError):
    pass


def _day(value: object) -> date | None:
    text = str(value).strip().replace("/", "-")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return datetime.strptime(text.split()[0], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            return None


def reference_range(source: ReportSource, start: date | None, end: date | None) -> tuple[date, date]:
    trades = [event.timestamp.date() for event in source.events if event.side in {"B", "S"}]
    events = [event.timestamp.date() for event in source.events]
    start = start or _day(source.period_start) or (min(trades or events) if events else None)
    end = end or _day(source.period_end) or (max(events) if events else None)
    if start is None or end is None or start > end:
        raise BuyHoldError("報表沒有可用的 Buy&Hold 日期區間。")
    return start, end


def _fetch_rows(dataset: str, code: str, start: date, end: date) -> list[dict]:
    token = os.getenv("FINMIND_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = httpx.get("https://api.finmindtrade.com/api/v4/data", headers=headers,
                             params={"dataset": dataset, "data_id": code,
                                     "start_date": start.isoformat(), "end_date": end.isoformat()}, timeout=20)
        response.raise_for_status()
        document = response.json()
        if not isinstance(document, dict) or document.get("status") not in {None, 200, "200"}:
            raise BuyHoldError("Buy&Hold 行情服務暫時無法提供資料，請稍後再試。")
        rows = document.get("data")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise BuyHoldError("Buy&Hold 行情資料格式錯誤。")
        return rows
    except (httpx.HTTPError, ValueError) as exc:
        if isinstance(exc, BuyHoldError):
            raise
        raise BuyHoldError("Buy&Hold 行情讀取失敗，請檢查代碼或稍後再試。") from exc


@lru_cache(maxsize=128)
def _market_data(product: str, code: str, start: date, end: date, cache_hour: int) -> tuple[list[dict], list[dict]]:
    # Bounded, hourly cache: changing strategy capital/mode never triggers another market request.
    if product == "期貨":
        return _fetch_rows("TaiwanFuturesDaily", code, start, end), []
    prices = _fetch_rows("TaiwanStockPrice", code, start, end)
    # FinMind's dividend `date` is the record date, not the ex-dividend date.
    # Include surrounding records, then apply only ex-dates within the holding period.
    dividend_start = date.fromordinal(max(date.min.toordinal(), start.toordinal() - 366))
    dividend_end = date.fromordinal(min(date.max.toordinal(), end.toordinal() + 366))
    dividends = _fetch_rows("TaiwanStockDividend", code, dividend_start, dividend_end)
    return prices, dividends


def _number(value: object) -> Decimal:
    try:
        result = Decimal(str(value).replace(",", ""))
        return result if result.is_finite() else Decimal(0)
    except InvalidOperation:
        return Decimal(0)


def _stock_curve(rows: list[dict], dividends: list[dict], start: date, end: date, capital: Decimal) -> list[dict]:
    prices = {_day(row.get("date")): _number(row.get("close")) for row in rows}
    points = sorted((day, price) for day, price in prices.items() if day and start <= day <= end and price > 0)
    if not points:
        raise BuyHoldError("指定區間內沒有可用的股票行情，請檢查代碼與日期。")
    cash_by_day: dict[date, Decimal] = defaultdict(Decimal)
    stock_by_day: dict[date, Decimal] = defaultdict(Decimal)
    seen = set()
    for row in dividends:
        cash_day = _day(row.get("CashExDividendTradingDate"))
        stock_day = _day(row.get("StockExDividendTradingDate"))
        cash = _number(row.get("CashEarningsDistribution")) + _number(row.get("CashStatutorySurplus"))
        stock = (_number(row.get("StockEarningsDistribution")) + _number(row.get("StockStatutorySurplus"))) / 10
        key = (cash_day, stock_day, cash, stock)
        if key in seen:
            continue
        seen.add(key)
        if cash_day and cash > 0:
            cash_by_day[cash_day] += cash
        if stock_day and stock > 0:
            stock_by_day[stock_day] += stock
    quantity = capital / points[0][1]
    previous_day, previous_price = points[0]
    curve = [{"timestamp": previous_day.isoformat(), "equity": float(capital), "profit": 0.0}]
    for day, price in points[1:]:
        cash = sum((value for ex_day, value in cash_by_day.items() if previous_day < ex_day <= day), Decimal(0))
        bonus = sum((value for ex_day, value in stock_by_day.items() if previous_day < ex_day <= day), Decimal(0))
        dividend_cash = quantity * cash
        quantity *= 1 + bonus
        # Match Visual Portfolio's split recognition (2–20x, within 8%).
        ratio = (previous_price - cash) / (1 + bonus) / price
        split = round(ratio)
        if 2 <= split <= 20 and abs(ratio - split) / split <= Decimal("0.08"):
            quantity *= split
        quantity += dividend_cash / price
        equity = quantity * price
        curve.append({"timestamp": day.isoformat(), "equity": float(equity), "profit": float(equity - capital)})
        previous_day, previous_price = day, price
    return curve


def _futures_curve(rows: list[dict], start: date, end: date, capital: Decimal, leverage: Decimal) -> list[dict]:
    prices: dict[date, dict[str, Decimal]] = defaultdict(dict)
    for row in rows:
        day = _day(row.get("date"))
        contract = str(row.get("contract_date", ""))
        if not day or not start <= day <= end or row.get("trading_session") not in {None, "", "position"}:
            continue
        # Ignore spread/weekly contracts; use the nearest monthly contract.
        if len(contract) != 6 or not contract.isdigit() or contract < day.strftime("%Y%m"):
            continue
        price = _number(row.get("close"))
        if price <= 0:
            price = _number(row.get("settlement_price"))
        if price > 0:
            prices[day][contract] = price
    if not prices:
        raise BuyHoldError("指定區間內沒有可用的期貨行情，請檢查代碼與日期。")
    curve = []
    previous = {}
    active = ""
    equity = capital
    quantity = Decimal(0)
    for day, contracts in sorted(prices.items()):
        contract = min(contracts)
        price = contracts[contract]
        if not previous:
            quantity = capital * leverage / price
        else:
            # Roll at the previous session's prices so the contract spread is not a return.
            if contract not in previous:
                raise BuyHoldError("期貨轉倉行情不完整，暫時無法計算 Buy&Hold。")
            prior_price = previous[active] if contract == active else previous[contract]
            equity += quantity * (price - prior_price)
        curve.append({"timestamp": day.isoformat(), "equity": float(equity), "profit": float(equity - capital)})
        previous, active = contracts, contract
    return curve


def analyze_buy_hold(source: ReportSource, settings: BuyHoldSettings | None,
                     start: date | None = None, end: date | None = None) -> dict | None:
    if settings is None:
        return None
    result = {"name": settings.name, "curve": [], "error": None}
    try:
        start, end = reference_range(source, start, end)
        result.update(requested_start=start.isoformat(), requested_end=end.isoformat())
        rows, dividends = _market_data(settings.product_type, settings.code, start, end, int(time.monotonic() // 3600))
        capital = settings.amount_wan * 10000
        curve = (_stock_curve(rows, dividends, start, end, capital) if settings.product_type == "股票"
                 else _futures_curve(rows, start, end, capital, settings.leverage))
        result.update(curve=curve, initial_capital=float(capital), start_date=curve[0]["timestamp"],
                      end_date=curve[-1]["timestamp"], final_capital=curve[-1]["equity"])
    except BuyHoldError as exc:
        # A missing reference must not hide the strategy's own report.
        result["error"] = str(exc)
    return result
