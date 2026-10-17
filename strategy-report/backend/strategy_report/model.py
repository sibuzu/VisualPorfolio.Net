from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class TradeEvent:
    index: int
    timestamp: datetime
    side: str
    quantity: Decimal
    price: Decimal
    symbol: str
    strategy_index: int = 1
    tag: str = ""
    kind: str = ""
    atr: Decimal = Decimal(0)

    @property
    def signed_quantity(self) -> Decimal:
        return self.quantity if self.side == "B" else -self.quantity if self.side == "S" else Decimal(0)


@dataclass(frozen=True)
class ReportSource:
    source_format: str
    filename: str
    strategy: str
    symbol: str
    params: dict[str, str]
    strategy_params: dict[str, str]
    events: tuple[TradeEvent, ...]
    point_value: Decimal = Decimal(1)
    slippage: str = "0"
    initial_capital: Decimal | None = None
    period_start: str = ""
    period_end: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


class ReportFormatError(ValueError):
    """User supplied report cannot be read safely or has an invalid format."""
