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


# Contract values in NTD per index point (TAIFEX contract specifications).
FUTURES_POINT_VALUES = {
    "TX": Decimal(200), "MTX": Decimal(50), "TMF": Decimal(10),
    "TE": Decimal(4000), "TF": Decimal(1000),
}


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


def _stock_history(rows: list[dict], dividends: list[dict], start: date, end: date,
                   capital: Decimal, code: str = "") -> tuple[list[dict], list[dict]]:
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
    detail = [{"timestamp": previous_day.isoformat(), "symbol": code, "side": "B",
               "quantity": float(quantity), "price": float(previous_price), "position": float(quantity),
               "profit": 0.0, "equity": float(capital), "action": "買進"}]
    previous_equity = capital
    for day, price in points[1:]:
        cash = sum((value for ex_day, value in cash_by_day.items() if previous_day < ex_day <= day), Decimal(0))
        bonus = sum((value for ex_day, value in stock_by_day.items() if previous_day < ex_day <= day), Decimal(0))
        dividend_cash = quantity * cash
        quantity *= 1 + bonus
        # Match Visual Portfolio's split recognition (2–20x, within 8%).
        ratio = (previous_price - cash) / (1 + bonus) / price
        split = round(ratio)
        is_split = 2 <= split <= 20 and abs(ratio - split) / split <= Decimal("0.08")
        if is_split:
            quantity *= split
        quantity += dividend_cash / price
        equity = quantity * price
        events = []
        if bonus > 0 and cash > 0:
            events.append("除權息")
        elif bonus > 0:
            events.append("除權")
        elif cash > 0:
            events.append("除息")
        if is_split:
            events.append("分割")
        action = "／".join(events) if events else "淨值"
        curve.append({"timestamp": day.isoformat(), "equity": float(equity), "profit": float(equity - capital)})
        detail.append({"timestamp": day.isoformat(), "symbol": code, "side": "M",
                       "quantity": float(quantity), "price": float(price), "position": float(quantity),
                       "profit": float(equity - previous_equity), "equity": float(equity), "action": action})
        previous_equity = equity
        previous_day, previous_price = day, price
    _close_history(detail, quantity)
    return curve, detail


def _stock_curve(rows: list[dict], dividends: list[dict], start: date, end: date, capital: Decimal) -> list[dict]:
    return _stock_history(rows, dividends, start, end, capital)[0]


def _close_history(detail: list[dict], quantity: Decimal) -> None:
    if len(detail) == 1:
        detail.append({**detail[0], "side": "S", "position": 0.0, "profit": 0.0, "action": "賣出"})
    else:
        prior_action = detail[-1]["action"]
        action = "賣出" if prior_action == "淨值" else f"{prior_action}／賣出"
        detail[-1].update(side="S", position=0.0, action=action)
    detail[-1]["quantity"] = float(quantity)


def _futures_history(rows: list[dict], start: date, end: date, capital: Decimal,
                     leverage: Decimal, code: str = "TX") -> tuple[list[dict], list[dict]]:
    point_value = FUTURES_POINT_VALUES.get(code)
    if point_value is None:
        raise BuyHoldError(f"期貨代碼 {code} 尚未設定每點價值，無法計算口數。")
    prices: dict[date, dict[str, tuple[Decimal, str]]] = defaultdict(dict)
    for row in rows:
        day = _day(row.get("date"))
        contract = str(row.get("contract_date", ""))
        if not day or not start <= day <= end or row.get("trading_session") not in {None, "", "position"}:
            continue
        # Ignore spread/weekly contracts; use the nearest monthly contract.
        if len(contract) != 6 or not contract.isdigit() or contract < day.strftime("%Y%m"):
            continue
        price = _number(row.get("close"))
        price_basis = "收盤"
        if price <= 0:
            price = _number(row.get("settlement_price"))
            price_basis = "結算"
        if price > 0:
            prices[day][contract] = (price, price_basis)
    if not prices:
        raise BuyHoldError("指定區間內沒有可用的期貨行情，請檢查代碼與日期。")
    curve = []
    detail = []
    trading_days = sorted(prices.items())
    active = min(trading_days[0][1])
    previous_price = None
    equity = capital
    quantity = Decimal(0)
    for index, (day, contracts) in enumerate(trading_days):
        if active not in contracts:
            raise BuyHoldError(f"{day.isoformat()} 舊合約 {active} 缺少平倉行情，無法計算 Buy&Hold。")
        price, price_basis = contracts[active]
        if previous_price is None:
            # Keep fractional contracts for an exact target leverage. P&L is
            # index-point movement times contracts times NTD per index point.
            quantity = capital * leverage / (price * point_value)
            daily_profit = Decimal(0)
        else:
            daily_profit = quantity * point_value * (price - previous_price)
            equity += daily_profit
        curve.append({"timestamp": day.isoformat(), "equity": float(equity), "profit": float(equity - capital)})
        detail.append({"timestamp": day.isoformat(), "symbol": code,
                       "side": "B" if previous_price is None else "M", "quantity": float(quantity),
                       "price": float(price), "position": float(quantity), "profit": float(daily_profit),
                       "equity": float(equity), "action": "買進" if previous_price is None else "淨值",
                       "contract": active, "price_basis": price_basis})
        if equity <= 0:
            detail[-1].update(side="S", position=0.0, action="資金耗盡")
            break
        if index + 1 < len(trading_days):
            next_active = min(trading_days[index + 1][1])
            if next_active != active:
                if next_active not in contracts:
                    raise BuyHoldError(f"{day.isoformat()} 新合約 {next_active} 缺少換倉行情，無法計算 Buy&Hold。")
                # Execute both legs at the same day's closes. The price gap
                # between contracts is not a gain or loss to the portfolio.
                detail[-1].update(side="S", position=0.0, action="換倉賣出")
                next_price, next_basis = contracts[next_active]
                detail.append({"timestamp": day.isoformat(), "symbol": code, "side": "B",
                               "quantity": float(quantity), "price": float(next_price),
                               "position": float(quantity), "profit": 0.0, "equity": float(equity),
                               "action": "換倉買進", "contract": next_active, "price_basis": next_basis})
                active, previous_price = next_active, next_price
                continue
        previous_price = price
    if detail[-1]["action"] != "資金耗盡":
        _close_history(detail, quantity)
    return curve, detail


def _futures_curve(rows: list[dict], start: date, end: date, capital: Decimal, leverage: Decimal) -> list[dict]:
    return _futures_history(rows, start, end, capital, leverage)[0]


def _performance(curve: list[dict], capital: Decimal) -> dict:
    """Build the compound-summary figures from one close per trading day."""
    points = [(date.fromisoformat(row["timestamp"][:10]), Decimal(str(row["equity"]))) for row in curve]
    peak = capital
    peak_day = points[0][0]
    maximum_drawdown = Decimal(0)
    maximum_drawdown_pct = Decimal(0)
    episodes = []
    episode = None
    previous = capital
    records = []
    for day, equity in points:
        records.append((day, equity - previous, equity))
        previous = equity
        if equity >= peak:
            if episode is not None:
                episode["recovered_at"] = day.isoformat()
                episodes.append(episode)
                episode = None
            peak, peak_day = equity, day
        drawdown = peak - equity
        drawdown_pct = drawdown / peak * 100 if peak > 0 else Decimal(0)
        maximum_drawdown = max(maximum_drawdown, drawdown)
        maximum_drawdown_pct = max(maximum_drawdown_pct, drawdown_pct)
        if drawdown > 0 and (episode is None or drawdown > episode["amount"]):
            episode = {"amount": drawdown, "percent": drawdown_pct,
                       "started_at": peak_day.isoformat(), "bottomed_at": day.isoformat(),
                       "recovered_at": None}
    if episode is not None:
        episodes.append(episode)
    episodes.sort(key=lambda row: row["percent"], reverse=True)
    drawdowns = [{**row, "amount": float(row["amount"]), "percent": float(row["percent"])}
                 for row in episodes[:5]]

    periods = {}
    for name, key in (("annual", lambda day: str(day.year)),
                      ("semiannual", lambda day: f"{day.year}/H{(day.month - 1) // 6 + 1}"),
                      ("quarterly", lambda day: f"{day.year}/Q{(day.month - 1) // 3 + 1}"),
                      ("monthly", lambda day: day.strftime("%Y/%m"))):
        groups = {}
        for record in records:
            groups.setdefault(key(record[0]), []).append(record)
        rows = []
        running = capital
        for period, group in groups.items():
            period_peak = running
            mdd = mdd_pct = Decimal(0)
            for _, _, equity in group:
                period_peak = max(period_peak, equity)
                decline = period_peak - equity
                if decline > mdd:
                    mdd = decline
                    mdd_pct = decline / period_peak * 100 if period_peak > 0 else Decimal(0)
            ending = group[-1][2]
            profit = ending - running
            rows.append({"period": period, "profit": float(profit), "cumulative": float(ending),
                         "return_pct": float(profit / running * 100) if running != 0 else 0.0,
                         "mdd": float(mdd), "mdd_pct": float(mdd_pct)})
            running = ending
        periods[name] = rows

    first_day, final_day = points[0][0], points[-1][0]
    final = points[-1][1]
    years = (final_day - first_day).days / 365
    annual_return = ((final / capital) ** (Decimal(1) / Decimal(str(years))) - 1) * 100 \
        if years > 0 and final > 0 else Decimal(-100) if years > 0 and final <= 0 else Decimal(0)
    summary = {"initial_capital": float(capital), "final_capital": float(final),
               "net_profit": float(final - capital), "start_date": first_day.isoformat(),
               "end_date": final_day.isoformat(), "annual_return_pct": float(annual_return),
               "max_drawdown": float(maximum_drawdown), "max_drawdown_pct": float(maximum_drawdown_pct)}
    return {"summary": summary, "drawdowns": drawdowns, "periods": periods}


def analyze_buy_hold(source: ReportSource, settings: BuyHoldSettings | None,
                     start: date | None = None, end: date | None = None) -> dict | None:
    if settings is None:
        return None
    result = {"name": settings.name, "curve": [], "detail": [], "error": None}
    try:
        start, end = reference_range(source, start, end)
        result.update(requested_start=start.isoformat(), requested_end=end.isoformat())
        rows, dividends = _market_data(settings.product_type, settings.code, start, end, int(time.monotonic() // 3600))
        capital = settings.amount_wan * 10000
        curve, detail = (_stock_history(rows, dividends, start, end, capital, settings.code)
                         if settings.product_type == "股票"
                         else _futures_history(rows, start, end, capital, settings.leverage, settings.code))
        result.update(curve=curve, detail=detail, initial_capital=float(capital), start_date=curve[0]["timestamp"],
                      end_date=curve[-1]["timestamp"], final_capital=curve[-1]["equity"],
                      **_performance(curve, capital))
        if detail[-1]["action"] == "資金耗盡":
            result["error"] = (f"{curve[-1]['timestamp']} 收盤後淨值 {curve[-1]['equity']:,.0f} 元，"
                               "資金已耗盡；Buy&Hold 自該日起停止計算。")
    except BuyHoldError as exc:
        # A missing reference must not hide the strategy's own report.
        result["error"] = str(exc)
    return result
