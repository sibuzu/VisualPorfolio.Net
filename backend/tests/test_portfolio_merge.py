from datetime import datetime

from backend.services.parser import TradeItem
from backend.services.portfolio import merge_trades


def _t(idx: int, ts: str, pnl: float, bs: str, contract: float, strategy_index: int) -> TradeItem:
    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    return TradeItem(
        idx=idx,
        trade_date1=dt,
        trade_date2=dt,
        profit=pnl,
        net_profit=pnl,
        trade_amount=0.0,
        bs=bs,
        contract=contract,
        price1=0.0,
        price2=0.0,
        point_value=1.0,
        strategy_index=strategy_index,
    )


def test_merge_trades_range_skips_carried_position_until_flat():
    strategy_trades = [
        (
            [
                _t(1, "2024-01-01 09:00:00", 0.0, "B", 1.0, 0),
                _t(2, "2024-01-10 09:00:00", 100.0, "S", 1.0, 0),  # closes position carried from pre-range
                _t(3, "2024-01-11 09:00:00", 10.0, "B", 1.0, 0),
                _t(4, "2024-01-12 09:00:00", 20.0, "S", 1.0, 0),
            ],
            {"weight": 1.0, "contract": 1.0},
        )
    ]

    out = merge_trades(strategy_trades, start=datetime(2024, 1, 5), end=None, factor=1.0)
    assert [x["trade_date2"] for x in out] == ["2024-01-11 09:00:00", "2024-01-12 09:00:00"]
    assert [x["net_profit"] for x in out] == [10.0, 20.0]


def test_merge_trades_range_keeps_flat_strategy_from_start():
    strategy_trades = [
        (
            [
                _t(1, "2024-01-01 09:00:00", 0.0, "B", 1.0, 0),
                _t(2, "2024-01-10 09:00:00", 100.0, "S", 1.0, 0),
            ],
            {"weight": 1.0, "contract": 1.0},
        ),
        (
            [
                _t(1, "2024-01-09 09:00:00", 5.0, "B", 1.0, 1),
                _t(2, "2024-01-09 13:45:00", 8.0, "S", 1.0, 1),
            ],
            {"weight": 1.0, "contract": 1.0},
        ),
    ]

    out = merge_trades(strategy_trades, start=datetime(2024, 1, 5), end=None, factor=1.0)
    assert [x["strategy_index"] for x in out] == [1, 1]
    assert [x["net_profit"] for x in out] == [5.0, 8.0]
