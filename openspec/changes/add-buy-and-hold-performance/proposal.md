## Why

Strategy portfolio management needs a fast way to add a benchmark-style buy-and-hold performance series without manually preparing daily returns. This lets users compare uploaded or calculated strategy performance against stock or futures holding behavior from a selected entry date.

## What Changes

- Add a `+ Buy&Hold` action to the strategy portfolio management controls, shown alongside `+新增績效` and `上傳專案` across two rows.
- Add a Buy&Hold creation dialog for date, amount in ten-thousand units, product type, code, and futures leverage.
- Show the leverage input only when futures is selected, with default value `5`.
- Create generated performance names using `BH{代碼}_{金額}萬` for stocks and `BH{代碼}_{金額}萬_{槓桿}X` for futures.
- Remember the last-used Buy&Hold dialog settings for the next time the dialog opens.
- Overwrite an existing generated Buy&Hold file when the same generated name is created again.
- Fetch market data through FinMind and generate a daily floating performance series from the selected buy date through the most recent available date.
- Allow fractional stock or futures positions at buy time to simplify position sizing.
- Support stock buy-and-hold with dividend reinvestment.
- Support futures buy-and-hold with rollover.
- Add contextual help text for the Buy&Hold dialog.

## Capabilities

### New Capabilities
- `buy-and-hold-performance`: Covers creating stock and futures buy-and-hold performance series from FinMind data, including UI behavior, generated naming, daily floating results, dividend reinvestment, futures leverage, and rollover.

### Modified Capabilities

## Impact

- Frontend strategy portfolio management controls and Buy&Hold modal/dialog UX.
- Backend service/API for generating and storing a Buy&Hold performance series.
- FinMind data access for Taiwan stock prices, dividend events, and futures price/rollover data.
- Tests for input handling, generated naming, data calculation, and UI visibility rules.
