from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, ROUND_HALF_UP
from math import sqrt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .model import ReportSource, TradeEvent
from .buy_hold import BuyHoldSettings


Mode = Literal[
    "backtest", "dynamic_compounding", "fixed_quantity", "risk_factor", "target_leverage", "profit_step",
    "fixed_amount", "fixed_risk", "profit_risk", "target_margin", "kelly",
]


class CalculationSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")

    mode: Mode = "fixed_quantity"
    initial_capital: Decimal = Field(default=Decimal(1_000_000), gt=0)
    backtest_initial_capital: Decimal | None = Field(default=None, gt=0)
    dynamic_initial_ratio: Decimal = Field(default=Decimal("0.10"), ge=0)
    dynamic_add_ratio: Decimal = Field(default=Decimal("0.15"), ge=0)
    dynamic_profit_threshold: Decimal = Field(default=Decimal(100_000_000), ge=0)
    dynamic_drawdown_threshold: str = "2000"
    dynamic_max_multiple: Decimal = Field(default=Decimal(10), ge=0)
    dynamic_interval: Literal["weekly", "monthly"] = "weekly"
    dynamic_lot_rounding: Literal["floor", "ceil", "round", "retain"] = "retain"
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
        raw = self.dynamic_drawdown_threshold.strip().removesuffix("%").strip()
        try:
            threshold = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("dynamic_drawdown_threshold must be a number in 萬 or a percent") from exc
        if not threshold.is_finite() or threshold < 0:
            raise ValueError("dynamic_drawdown_threshold must be nonnegative")
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


def _run_events(source: ReportSource, cfg: CalculationSettings, *, compound: bool,
                initial_override: Decimal | None = None) -> tuple[list[dict], Decimal]:
    initial = initial_override if initial_override is not None else (
        (cfg.backtest_initial_capital or source.initial_capital or Decimal(100_000))
        if cfg.mode == "backtest" else cfg.initial_capital)
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
            elif event.kind == "x":
                multiplier = steps[-1]["multiplier"] if steps else Decimal(1)
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
            "open_position": max((abs(position) for position in positions.values()), default=Decimal(0)),
            "strategy_position": open_trade.get(key, {}).get("position", Decimal(0)),
            "multiplier": multiplier,
            "profit": profit, "net": net, "equity": initial + net if compound else net,
        })
    return steps, initial


def _range_source(source: ReportSource, cfg: CalculationSettings) -> ReportSource:
    """Prepare trades before calculating, following C# GetListTradeRecord.

    Track each strategy/symbol separately so overlapping positions do not reset
    one another. A carried position starts at a price mark, its reversal, or the
    next entry after it has closed. Never manufacture an exit at the end date.
    """
    first = (cfg.date_start or date.min) if cfg.date_range_enabled is not False else date.min
    last = (cfg.date_end or date.max) if cfg.date_range_enabled is not False else date.max
    positions: dict[tuple[int, str], Decimal] = defaultdict(Decimal)
    waiting: dict[tuple[int, str], Decimal] = {}
    selected: list[TradeEvent] = []
    for event in source.events:
        day = event.timestamp.date()
        if day > last:
            break
        key = (event.strategy_index, event.symbol)
        positions[key] += event.signed_quantity
        position = positions[key]
        if day < first:
            waiting[key] = position
            continue
        carried = waiting.get(key, Decimal(0))
        if carried:
            if position == 0:
                waiting.pop(key, None)
            elif event.side not in {"B", "S"} and event.price != 0 and position * carried > 0:
                selected.append(replace(event, side="B" if position > 0 else "S",
                                        quantity=abs(position), kind="x"))
                selected.append(event)
                waiting.pop(key, None)
            elif position * carried < 0:
                selected.append(replace(event, quantity=abs(position)))
                waiting.pop(key, None)
            continue
        selected.append(event)
    return replace(source, events=tuple(selected))


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
    recent_positions = [Decimal(0)] * 3
    for index, step in enumerate(steps):
        event = step["event"]
        recent_positions[index % len(recent_positions)] = step["open_position"]
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
            "open_position": max(recent_positions),
            "ref_price": event.price,
            "skip": not is_trade,
        })
    return records


def _periods(records: list[dict], starting: Decimal, compound: bool) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = {}
    keys = {
        "annual": lambda dt: f"{dt.year}",
        "semiannual": lambda dt: f"{dt.year}/H{(dt.month - 1) // 6 + 1}",
        "quarterly": lambda dt: f"{dt.year}/Q{(dt.month - 1) // 3 + 1}",
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
            peak, equity, mdd, mdd_pct = running, running, Decimal(0), Decimal(0)
            for record in period_records:
                equity += record["profit"]
                peak = max(peak, equity)
                drawdown = peak - equity
                if drawdown > mdd:
                    mdd = drawdown
                    mdd_pct = drawdown / peak * 100 if peak > 0 else Decimal(0)
            running += profit
            rows.append({"period": period, "profit": float(profit), "cumulative": float(running),
                         "return_pct": float(rate), "mdd": float(mdd), "mdd_pct": float(mdd_pct)})
        output[name] = rows
    return output


def _dynamic_compounding_records(simple_records: list[dict], source: ReportSource,
                                 cfg: CalculationSettings) -> tuple[list[dict], list[dict]]:
    """Scale C# simple-profit records with one multiplier per week or month."""
    initial = cfg.initial_capital
    drawdown = strategy_mdd = Decimal(0)
    for row in simple_records:
        drawdown = min(Decimal(0), drawdown + row["profit"])
        strategy_mdd = max(strategy_mdd, -drawdown)
    base_capital = initial * cfg.dynamic_initial_ratio
    if base_capital <= 0:
        base_capital = initial
    base_mdd = strategy_mdd if strategy_mdd > 0 else base_capital
    max_risk = base_capital * cfg.dynamic_max_multiple
    threshold_text = cfg.dynamic_drawdown_threshold.strip()
    threshold_percent = threshold_text.endswith("%")
    threshold_value = Decimal(threshold_text.removesuffix("%").strip())
    if threshold_percent and threshold_value > 1:
        threshold_value /= 100

    equity = logic_peak = recovery_peak = initial
    adding = waiting_recovery = entered_add = False
    current_period: date | None = None
    multiplier = Decimal(1)
    records: list[dict] = []
    detail: list[dict] = []

    def advance() -> None:
        nonlocal adding, waiting_recovery, entered_add, recovery_peak
        threshold = logic_peak * threshold_value if threshold_percent else threshold_value * 10_000
        if adding:
            if logic_peak - equity > threshold:
                adding = False
                waiting_recovery = True
                recovery_peak = logic_peak
        elif waiting_recovery:
            if equity > recovery_peak:
                adding = True
                waiting_recovery = False
        elif not entered_add and equity - initial > cfg.dynamic_profit_threshold:
            adding = True
            entered_add = True

    for index, row in enumerate(simple_records, start=1):
        timestamp = row["timestamp"]
        day = timestamp.date()
        period = day.replace(day=1) if cfg.dynamic_interval == "monthly" else day - timedelta(days=day.weekday())
        if period != current_period:
            if current_period is not None:
                advance()
            current_period = period
            ratio = cfg.dynamic_add_ratio if adding else cfg.dynamic_initial_ratio
            risk = equity * ratio
            if max_risk > 0:
                risk = min(risk, max_risk)
            multiplier = max(Decimal(0), risk / base_mdd) if base_mdd > 0 else Decimal(1)
            rounding = {
                "floor": ROUND_FLOOR, "ceil": ROUND_CEILING, "round": ROUND_HALF_UP,
            }.get(cfg.dynamic_lot_rounding)
            if rounding:
                multiplier = multiplier.to_integral_value(rounding=rounding)
        profit = row["profit"] * multiplier
        equity += profit
        logic_peak = max(logic_peak, equity)
        records.append({**row, "profit": profit, "equity": equity, "multiplier": multiplier})
        detail.append({
            "index": index, "strategy": 0,
            "timestamp": timestamp.isoformat(sep=" "), "symbol": source.symbol,
            "side": "N", "quantity": float(multiplier), "price": float(row["ref_price"]),
            "position": float(multiplier), "profit": float(profit), "equity": float(equity),
            "multiplier": float(multiplier),
            "action": "動態複利(ByMonth)" if cfg.dynamic_interval == "monthly" else "動態複利(ByWeek)",
        })
    return records, detail


def _section(source: ReportSource, cfg: CalculationSettings, *, compound: bool) -> dict:
    detail: list[dict] = []
    if compound and cfg.mode == "dynamic_compounding":
        simple_steps, _ = _run_events(_range_source(source, cfg), cfg, compound=False)
        records, detail = _dynamic_compounding_records(_profit_records(simple_steps, False), source, cfg)
        steps: list[dict] = []
        initial = cfg.initial_capital
    else:
        initial_override = None
        if compound and cfg.mode == "backtest" and cfg.date_start and cfg.date_range_enabled is not False:
            earlier = replace(source, events=tuple(event for event in source.events
                                                   if event.timestamp.date() < cfg.date_start))
            earlier_steps, initial = _run_events(earlier, cfg, compound=True)
            initial_override = earlier_steps[-1]["equity"] if earlier_steps else initial
        steps, initial = _run_events(_range_source(source, cfg), cfg, compound=compound,
                                    initial_override=initial_override)
        records = _profit_records(steps, compound)
    starting = initial if compound else Decimal(0)
    peak = starting
    maximum_drawdown = Decimal(0)
    maximum_drawdown_pct = Decimal(0)
    curve: list[dict] = []
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
            "open_position": float(record.get("open_position", 0)),
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
