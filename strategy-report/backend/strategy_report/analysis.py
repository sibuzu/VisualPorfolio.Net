from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN
from math import sqrt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .model import ReportSource, TradeEvent
from .buy_hold import BuyHoldSettings


Mode = Literal[
    "backtest", "fixed_quantity", "risk_factor", "target_leverage", "profit_step",
    "fixed_amount", "fixed_risk", "profit_risk", "target_margin", "kelly",
]


class CalculationSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")

    mode: Mode = "fixed_quantity"
    initial_capital: Decimal = Field(default=Decimal(1_000_000), gt=0)
    fixed_quantity: Decimal = Field(default=Decimal(1), ge=0)
    risk_factor: Decimal = Field(default=Decimal("0.002"), ge=0)
    leverage: Decimal = Field(default=Decimal("0.2"), ge=0, le=100)
    leverage_funds: Literal["fixed", "cumulative"] = "cumulative"
    initial_quantity: Decimal = Field(default=Decimal(50), ge=0)
    minimum_quantity: Decimal = Field(default=Decimal(0), ge=0)
    profit_base: Decimal = Field(default=Decimal(100_000), gt=0)
    amount_per_quantity: Decimal = Field(default=Decimal(400_000), gt=0)
    fixed_risk_ratio: Decimal = Field(default=Decimal("0.02"), ge=0)
    initial_risk_ratio: Decimal = Field(default=Decimal("0.02"), ge=0)
    profit_risk_ratio: Decimal = Field(default=Decimal("0.05"), ge=0)
    loss_per_trade: Decimal = Field(default=Decimal(10_000), gt=0)
    margin_ratio: Decimal = Field(default=Decimal("0.1"), ge=0)
    margin_per_quantity: Decimal = Field(default=Decimal(100_000), gt=0)
    stake_percent: Decimal = Field(default=Decimal(10), ge=0)
    chip_size: Decimal = Field(default=Decimal(0), ge=0)
    maximum_quantity: Decimal = Field(default=Decimal(0), ge=0)
    integer_quantity: bool = False
    date_start: date | None = None
    date_end: date | None = None
    date_range_enabled: bool | None = None
    buy_hold: BuyHoldSettings | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise ValueError("date_start must be on or before date_end")
        if self.mode == "kelly" and self.chip_size <= 0:
            raise ValueError("chip_size must be positive for Kelly stake")
        return self


def _slippage(price: Decimal, text: str) -> Decimal:
    raw = str(text or "0").strip().replace("％", "%")
    if not raw:
        return Decimal(0)
    try:
        if raw.endswith("%"):
            return price * Decimal(raw[:-1]) / Decimal(100)
        return Decimal(raw)
    except Exception:
        return Decimal(0)


def _factor(cfg: CalculationSettings, source: ReportSource, capital: Decimal, event: TradeEvent, initial: Decimal) -> Decimal:
    if capital <= 0:
        return Decimal(0)
    amount = abs(event.price * event.quantity * source.point_value)
    profit = capital - initial
    mode = cfg.mode
    if mode == "backtest":
        return Decimal(1)
    if mode == "fixed_quantity":
        value = cfg.fixed_quantity
    elif mode == "profit_step":
        value = max(cfg.minimum_quantity, cfg.initial_quantity + profit / cfg.profit_base)
    elif mode == "target_leverage":
        funds = initial if cfg.leverage_funds == "fixed" else capital
        value = funds * cfg.leverage / amount if amount else Decimal(0)
    elif mode == "risk_factor":
        denom = event.atr * source.point_value
        value = (capital * cfg.risk_factor / denom).quantize(Decimal(1), rounding=ROUND_HALF_EVEN) if denom > 0 else Decimal(0)
    elif mode == "fixed_amount":
        value = capital / cfg.amount_per_quantity
    elif mode == "fixed_risk":
        value = (capital * cfg.fixed_risk_ratio / cfg.loss_per_trade).to_integral_value(rounding=ROUND_FLOOR)
    elif mode == "profit_risk":
        if profit <= 0:
            value = capital * cfg.initial_risk_ratio / cfg.loss_per_trade
        else:
            value = (initial * cfg.initial_risk_ratio + profit * cfg.profit_risk_ratio) / cfg.loss_per_trade
    elif mode == "target_margin":
        value = capital * cfg.margin_ratio / cfg.margin_per_quantity
    else:
        value = capital * cfg.stake_percent / Decimal(100) / cfg.chip_size
    if cfg.maximum_quantity > 0:
        value = min(value, cfg.maximum_quantity)
    if cfg.integer_quantity:
        value = value.to_integral_value(rounding=ROUND_FLOOR)
    return max(value, Decimal(0))


def _run_events(source: ReportSource, cfg: CalculationSettings, *, compound: bool) -> tuple[list[dict], Decimal]:
    initial = (source.initial_capital or Decimal(100_000)) if cfg.mode == "backtest" else cfg.initial_capital
    cash = Decimal(0)
    positions: dict[str, Decimal] = defaultdict(Decimal)
    last_prices: dict[str, Decimal] = {}
    open_trade: dict[tuple[int, str], dict[str, Decimal]] = {}
    realized_capital = initial
    pending_amount = Decimal(0)
    last_net = Decimal(0)
    steps: list[dict] = []

    for event in source.events:
        key = (event.strategy_index, event.symbol)
        open_row = open_trade.get(key)
        previous_position = open_row["position"] if open_row else Decimal(0)
        if compound:
            if cfg.mode == "backtest":
                multiplier = Decimal(1)
            elif previous_position != 0:
                multiplier = open_row["multiplier"]
            elif event.side in {"B", "S"}:
                multiplier = _factor(cfg, source, realized_capital, event, initial)
            else:
                multiplier = Decimal(1)
        else:
            multiplier = Decimal(1)

        quantity = event.quantity * multiplier if event.side in {"B", "S"} else Decimal(0)
        signed = quantity if event.side == "B" else -quantity if event.side == "S" else Decimal(0)
        if compound and event.kind != "x" and event.price != 0:
            pending_amount += quantity
        if event.price > 0 or signed != 0:
            last_prices[event.symbol] = event.price
        positions[event.symbol] += signed
        slip = Decimal(0) if event.kind == "x" else _slippage(event.price, source.slippage)
        if event.side == "B":
            cash -= quantity * (event.price + slip) * source.point_value
        elif event.side == "S":
            cash += quantity * (event.price - slip) * source.point_value

        net = cash
        for symbol, position in positions.items():
            mark = last_prices.get(symbol, Decimal(0))
            # Cash already includes this execution's cost. Open positions are marked
            # at market price; exit costs are charged only when the exit executes.
            net += position * mark * source.point_value
        profit = net - last_net
        last_net = net

        if compound and event.side in {"B", "S"} and quantity > 0:
            old = previous_position
            new = old + signed
            if old == 0 or old * signed > 0:
                old_abs = abs(old)
                avg = ((open_row["average"] * old_abs + event.price * quantity) / (old_abs + quantity)) if old_abs else event.price
            else:
                closed = min(abs(old), quantity)
                direction = Decimal(1) if old > 0 else Decimal(-1)
                realized_capital += ((event.price - open_row["average"]) * closed * direction
                                     - pending_amount * _slippage(event.price, source.slippage)) * source.point_value
                pending_amount = Decimal(0)
                avg = event.price if new * old < 0 else open_row["average"]
            if new == 0:
                open_trade.pop(key, None)
            else:
                open_trade[key] = {"position": new, "average": avg, "multiplier": multiplier}

        steps.append({
            "event": event, "quantity": quantity, "signed_quantity": signed,
            "position": positions[event.symbol],
            "strategy_position": open_trade.get(key, {}).get("position", Decimal(0)),
            "multiplier": multiplier,
            "profit": profit, "net": net, "equity": initial + net if compound else net,
        })
    return steps, initial


def _range_steps(steps: list[dict], cfg: CalculationSettings, initial: Decimal, compound: bool) -> tuple[list[dict], Decimal]:
    first = (cfg.date_start or date.min) if cfg.date_range_enabled is not False else date.min
    last = (cfg.date_end or date.max) if cfg.date_range_enabled is not False else date.max
    previous = initial if compound else Decimal(0)
    selected: list[dict] = []
    for step in steps:
        day = step["event"].timestamp.date()
        if day < first:
            previous = step["equity"]
        elif day <= last:
            selected.append(step)
    return selected, previous


def _ratio(values: list[Decimal], downside: bool, timestamps: list[datetime]) -> float:
    if len(values) < 2:
        return 0.0
    period_years = ((timestamps[-1] - timestamps[0]).days + 1) / 365.25
    if period_years <= 0:
        return 0.0
    numbers = [float(value) for value in values]
    mean = sum(numbers) / len(numbers)
    variance = (sum(value * value for value in numbers if value < 0) / len(numbers)) if downside else (
        sum((value - mean) ** 2 for value in numbers) / len(numbers)
    )
    return mean / sqrt(variance) * sqrt(len(numbers) / period_years) if variance > 0 else 0.0


def _profit_records(steps: list[dict], compound: bool) -> list[dict]:
    records: list[dict] = []
    for step in steps:
        event = step["event"]
        is_trade = event.side in {"B", "S"} and event.kind != "x"
        if compound and (event.price == 0 or (event.kind == "x" and step["profit"] == 0)):
            continue
        if not compound and records and abs((event.timestamp - records[-1]["timestamp"]).total_seconds()) < 1800:
            records[-1]["profit"] += step["profit"]
            records[-1]["skip"] = records[-1]["skip"] and not is_trade
            records[-1]["equity"] = step["equity"]
            continue
        records.append({
            "timestamp": event.timestamp,
            "profit": step["profit"],
            "equity": step["equity"],
            "ref_price": event.price,
            "skip": not is_trade,
        })
    return records


def _periods(records: list[dict], starting: Decimal, compound: bool) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = {}
    keys = {
        "annual": lambda dt: f"{dt.year}",
        "monthly": lambda dt: dt.strftime("%Y/%m"),
        "weekly": lambda dt: f"{dt.isocalendar().year}/W{dt.isocalendar().week:02d}",
        "daily": lambda dt: dt.strftime("%Y/%m/%d"),
    }
    for name, key_fn in keys.items():
        groups: dict[str, list[dict]] = {}
        for record in records:
            period = key_fn(record["timestamp"])
            groups.setdefault(period, []).append(record)
        running = starting
        rows: list[dict] = []
        for period, period_records in groups.items():
            profit = sum((record["profit"] for record in period_records), Decimal(0))
            rate = profit / running * 100 if compound and running != 0 else Decimal(0)
            peak, equity, mdd = running, running, Decimal(0)
            for record in period_records:
                equity += record["profit"]
                peak = max(peak, equity)
                mdd = max(mdd, peak - equity)
            running += profit
            rows.append({"period": period, "profit": float(profit), "cumulative": float(running), "return_pct": float(rate), "mdd": float(mdd)})
        output[name] = rows
    return output


def _section(source: ReportSource, cfg: CalculationSettings, *, compound: bool) -> dict:
    all_steps, initial = _run_events(source, cfg, compound=compound)
    steps, starting = _range_steps(all_steps, cfg, initial, compound)
    records = _profit_records(steps, compound)
    peak = starting
    maximum_drawdown = Decimal(0)
    maximum_drawdown_pct = Decimal(0)
    curve: list[dict] = []
    detail: list[dict] = []
    drawdown_episodes: list[dict] = []
    peak_time: datetime | None = None
    open_episode: dict | None = None
    for record in records:
        timestamp = record["timestamp"]
        equity = record["equity"]
        if equity >= peak:
            if open_episode is not None:
                open_episode["recovered_at"] = timestamp.isoformat(sep=" ")
                drawdown_episodes.append(open_episode)
                open_episode = None
            peak = equity
            peak_time = timestamp
        drawdown = peak - equity
        maximum_drawdown = max(maximum_drawdown, drawdown)
        drawdown_pct = drawdown / peak * 100 if peak > 0 else Decimal(0)
        maximum_drawdown_pct = max(maximum_drawdown_pct, drawdown_pct)
        if drawdown > 0 and (open_episode is None or drawdown > open_episode["amount"]):
            open_episode = {
                "amount": drawdown, "percent": drawdown_pct,
                "started_at": peak_time.isoformat(sep=" ") if peak_time else timestamp.isoformat(sep=" "),
                "bottomed_at": timestamp.isoformat(sep=" "), "recovered_at": None,
            }
        curve.append({
            "timestamp": timestamp.isoformat(sep=" "), "equity": float(equity),
            "profit": float(record["profit"]), "drawdown": float(drawdown), "drawdown_pct": float(drawdown_pct),
        })
    previous_detail_net = starting - initial if compound else starting
    for step in steps:
        event = step["event"]
        equity = step["equity"]
        if event.side in {"B", "S"} and event.kind != "x":
            detail_profit = step["profit"] if compound else step["net"] - previous_detail_net
            detail.append({
                "index": event.index + 1, "strategy": event.strategy_index,
                "timestamp": event.timestamp.isoformat(sep=" "), "symbol": event.symbol,
                "side": event.side, "quantity": float(step["quantity"]),
                "price": float(event.price), "position": float(step["strategy_position"] if compound else step["position"]),
                "profit": float(detail_profit), "equity": float(equity),
                "multiplier": float(step["multiplier"]), "action": event.tag,
            })
            previous_detail_net = step["net"]
    if open_episode is not None:
        drawdown_episodes.append(open_episode)
    drawdown_episodes.sort(key=lambda row: row["percent"] if compound else row["amount"], reverse=True)
    total_profit = sum((record["profit"] for record in records), Decimal(0))
    trade_count = sum(not record["skip"] for record in records)
    profits = [record["profit"] for record in records]
    timestamps = [record["timestamp"] for record in records]
    winning_profit = sum((profit for profit in profits if profit > 0), Decimal(0))
    losing_profit = sum((profit for profit in profits if profit <= 0), Decimal(0))
    winning_count = sum(profit > 0 for profit in profits)
    trade_amount = sum((record["ref_price"] for record in records if not record["skip"]), Decimal(0))
    summary = {
        "initial_capital": float(starting), "final_capital": float(starting + total_profit),
        "net_profit": float(total_profit), "average_net_profit": float(total_profit / trade_count) if trade_count else 0.0,
        "trade_count": trade_count, "max_drawdown": float(maximum_drawdown),
        "max_drawdown_pct": float(maximum_drawdown_pct),
        "profit_over_mdd": float(total_profit / maximum_drawdown) if maximum_drawdown else 0.0,
        "earning_power_pct": float(total_profit / trade_amount * 100) if trade_amount else 0.0,
        "big_point_value": float(source.point_value), "trade_cost": source.slippage,
        "win_rate_pct": winning_count / len(profits) * 100 if profits else 0.0,
        "profit_factor": float(-winning_profit / losing_profit) if losing_profit < 0 else 100.0,
        "winning_profit": float(winning_profit), "losing_profit": float(losing_profit),
        "winning_count": winning_count, "losing_count": sum(profit <= 0 for profit in profits),
        "sharpe_ratio": _ratio(profits, False, timestamps),
        "sortino_ratio": _ratio(profits, True, timestamps),
        "start_date": timestamps[0].date().isoformat() if timestamps else None,
        "end_date": timestamps[-1].date().isoformat() if timestamps else None,
    }
    if compound and timestamps:
        years = max((timestamps[-1] - timestamps[0]).days / 365, 0)
        final = starting + total_profit
        summary["annual_return_pct"] = float(((final / starting) ** (Decimal(1) / Decimal(str(years))) - 1) * 100) if years > 0 and starting > 0 and final > 0 else 0.0
    episodes = [{**row, "amount": float(row["amount"]), "percent": float(row["percent"])} for row in drawdown_episodes[:5]]
    return {"summary": summary, "curve": curve, "detail": detail, "periods": _periods(records, starting, compound), "drawdowns": episodes}


def source_date_range(source: ReportSource) -> dict[str, str | None]:
    dates = [event.timestamp.date() for event in source.events]
    return {"start": min(dates).isoformat() if dates else None,
            "end": max(dates).isoformat() if dates else None}


def analyze_report(source: ReportSource, cfg: CalculationSettings) -> dict:
    simple = _section(source, cfg, compound=False)
    compound = _section(source, cfg, compound=True)
    return {
        "source": {
            "filename": source.filename, "format": source.source_format,
            "strategy": source.strategy, "symbol": source.symbol,
            "event_count": len(source.events),
            "trade_count": sum(event.side in {"B", "S"} for event in source.events),
            "point_value": float(source.point_value), "slippage": source.slippage,
            "source_initial_capital": float(source.initial_capital) if source.initial_capital is not None else None,
            "params": source.params, "strategy_params": source.strategy_params,
            "date_range": source_date_range(source),
        },
        "settings": cfg.model_dump(mode="json"),
        "simple": simple, "compound": compound,
    }
