# C# StrategyReport parity inventory

Reference repository: `/home/jack/git/hft/src/Utilities/StrategyReport/` at `a896c69e` (.NET Framework 4.6 WinForms). Format examples: `/home/jack/git/sea_spec/examples/` at `3147682`. The local environment has neither `dotnet` nor `mono`, and no built `StrategyReport.exe`; numerical desktop output is still required for a C# golden comparison.

| Area | C# source | Web acceptance |
| --- | --- | --- |
| Inputs | `FormMain.LoadFile`, `ClsSeaFormat` | `.srp` XML and `.sea` ZIP containing `strategy.toml` and `events.jsonl` |
| Simple detail | `FormSimpleDetail.CreateSimpleDetails` | Chronological trade event rows: index, strategy, date, symbol, side/quantity, price, position, profit, accumulated profit, action; cash and mark-to-market net value per event |
| Simple summary | `ClsSummaryReport.CreateSummaryPart` | Period, symbol, strategy, trade time, net/average profit, trade count, earning power, point value, trade cost, Sharpe, Sortino, Profit/MDD, ranked MDD |
| Compound detail | `FormCompoundDetail.CreateCompoundDetails` | Same event columns after capital management, with quantity multiplier, compound profit, and current capital |
| Compound summary | `ClsSummaryReport.CreateCompoundPart` | Initial/final capital and quantity, management mode, annualized return, ranked MDD and mode parameters |
| Period tables | `ClsSummaryReport.CreaeteAnnualPart`, `CreaeteCompoundAnnualPart` | Annual, monthly, weekly and daily profit and cumulative totals; compound return where C# shows it |
| Charts | `FormSimplePlot`, `FormCompoundPlot`, `FormYearPlot` | Simple and compound equity/drawdown curves plus annual/monthly performance; reference plot can be added when an input supplies reference quotes |
| Date range | `FormCapitalManage.GetRangeStart/End`, `FormCompoundDetail.GetCompoundRangeStartCapital` | All dates or selected range; replay earlier events to obtain starting capital and open positions |
| Export | `FormSimpleDetail`, `FormCompoundDetail`, `FormMain.SaveStrategyResult` | CSV detail/period tables and browser print layout; only `.srp`/`.sea` input is in current Web scope |

## Capital management modes

`ClsCapitalManage` defines the calculation modes and defaults. It starts with fixed quantity, initial capital 1,000,000, and quantity 1. The mode `回測時已計算` uses source quantity without another multiplier, source `InitCapital` / `InitialCapital` / `初始資金`, or 100,000 when none exists.

| Mode | C# quantity basis / input |
| --- | --- |
| `回測時已計算` | Source quantity; multiplier 1 |
| `固定口數` | Fixed quantity, default 1 |
| `風險因子` | Rounded capital × risk factor / (ATR × point value), default factor 0.002 |
| `槓桿倍數目標` | Capital × leverage / absolute trade amount, with fixed or cumulative capital, default leverage 0.2 |
| `固定獲利一口` | Initial quantity + profit / profit base, floored by minimum quantity |
| `固定金額一口` | Capital / amount per quantity |
| `固定風險` | Floor(capital × risk ratio / loss per trade) |
| `獲利風險` | Initial capital and realized profit use separate risk ratios |
| `保證金目標` | Capital × margin target ratio / margin per quantity |
| `凱利投注` | Capital × stake percent / ChipSize |

All modes use the C# maximum quantity cap (0 means uncapped) and its optional integer quantity floor. The source currently forces the unified net-value-difference series on, and backtest-calculated mode ignores the maximum quantity cap.

## Paired fixtures selected

Start with `sea_spec/examples/srp/BDS/BDS.srp` plus sibling `events.jsonl` and `strategy.toml`; add `BDS_BTC` and `BDS_TXF` to cover different markets and point values. Package each sibling SEA project into a `.sea` archive for Web tests without modifying the reference repository. Use `TX時間沖` for a larger date-filter and repeated-trade fixture. The normalized event counts are 3057, 68, 212, and 6074 respectively, and all trade event fields match between the paired formats after normalizing the display symbol to its instrument ID.

Source-derived hand checks use a two-trade example with quantity 2, buy price 100, sell price 105, point value 200, no slippage, and backtest capital 80,000,000. Net profit is `(105 - 100) × 2 × 200 = 2,000`; final capital is 80,002,000. Reversing the exit price to 95 yields a 2,000 loss and final capital 79,998,000. Two overlapping 1-quantity strategies bought at 100 and sold at 105 yield the same 2,000 combined profit. A date range starting after a prior 2,000 win begins at 80,002,000, then adds only in-range profit. These expectations are independent arithmetic checks based on the C# cash/position formulas, not captured output from the desktop binary. Use exact equality for these integer examples and `1e-6` absolute tolerance for decimal fixture comparisons.

## Web acceptance results

The repository includes the paired `BDS_TXF.srp` / `BDS_TXF.sea` fixture. Its 212 normalized events, report sections, detail rows, equity curves, drawdown episodes, and period tables match exactly between the two formats for all ten modes. The source-derived positive, losing, overlapping, filtered, and slippage examples also pass. C# merges simple-profit events less than 30 minutes apart for its summary and charts; the Web implementation now does the same while retaining chronological detail rows.

| Mode | BDS_TXF simple net | BDS_TXF compound net | BDS_TXF final capital |
| --- | ---: | ---: | ---: |
| Backtest calculated | 276,780.44 | 276,780.44 | 376,780.44 |
| Fixed quantity | 276,780.44 | 276,780.44 | 1,276,780.44 |
| Risk factor | 276,780.44 | 0.00 | 1,000,000.00 |
| Target leverage | 276,780.44 | 10,086.59 | 1,010,086.59 |
| Profit step | 276,780.44 | -3,977,452.68 | -2,977,452.68 |
| Fixed amount | 276,780.44 | -1,224,470.03 | -224,470.03 |
| Fixed risk | 276,780.44 | -626,730.80 | 373,269.20 |
| Profit risk | 276,780.44 | -1,021,289.16 | -21,289.16 |
| Target margin | 276,780.44 | -221,318.91 | 778,681.09 |
| Kelly (ChipSize 100,000) | 276,780.44 | -221,318.91 | 778,681.09 |

These are Web fixture values, not desktop golden output. The risk-factor result is zero because this fixture does not supply ATR. C# weekly grouping follows the desktop system culture; the Web labels weeks using ISO weeks for a stable cross-platform display. The Web CSV and browser print layout replace the WinForms export and saved-report UI. Numerical comparison against actual C# desktop output remains unverified because the binary/runtime is unavailable locally.

### Execution-cost timing correction

Compound equity now marks open positions at market price, just like simple equity, without reserving an extra future exit cost. Actual entry and exit cash flows each charge their own execution cost. This intentionally supersedes the previous compound liquidation-price valuation: interim equity, drawdowns, and event profits reflect the new timing while a completed round trip retains its total cash profit for identical executed quantities. Regression tests cover long/short positions, absolute/percentage costs, scaled quantities, price-only marks, and exclusion of a carried position closing at the range start. SR-CWBKRR with multiplier 1 now displays its first two profits as -2,000 and -92,142 (first equity 998,000; second approximately 905,858).

### Date-range position preparation (C# e3edb51a)

Rechecked `FormMain.GetListTradeRecord` and `FormCompoundDetail` after pulling reference commit `e3edb51a`. C# now also charges execution costs separately without reserving exit costs, including its backtest range-start equity calculation. Web filters trades before calculations: skip carried positions until flat, establish a cost-free synthetic opening at a valid price mark, or retain only the new quantity on reversal. Web tracks this state per strategy/symbol to prevent overlapping positions from affecting each other (C# uses a single range-start state). Managed modes restart configured capital and sizing; only backtest mode carries pre-range equity. End dates retain open positions and last available marks without a forced close.

SR-CWBKRR, 2025-01-01 through 2026-10-24: both detail views begin at the 2025-01-02 13:30 buy at 1893.75, excluding the prior 09:00 closing sell; 116 detail executions remain. Fixed multiplier 1 entry cost is 2000. Regression coverage includes long/short carried positions, partial closes, price marks, reversals, overlapping strategies, range-end open positions, capital resets and the actual boundary prices/quantities. These are source-derived checks, not execution of the C# desktop binary.
