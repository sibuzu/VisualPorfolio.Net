## ADDED Requirements

### Requirement: Present simple strategy performance
Strategy Report SHALL display a simple strategy summary, equity and drawdown charts, annual/monthly/weekly/daily tables, and a chronological trade detail view based on one consistent event and profit series.

#### Scenario: View a strategy
- **WHEN** a valid `.srp` or `.sea` report is imported
- **THEN** the user SHALL be able to inspect summary metrics, period totals, charts, and the transactions that produce those values

#### Scenario: Filter date range
- **WHEN** the user selects a date range
- **THEN** displayed detail rows, period tables, and summary metrics SHALL reflect the selected range and show the effective start and end dates

### Requirement: Calculate capital managed performance
Strategy Report SHALL offer the C# StrategyReport capital management modes: backtest already calculated, fixed quantity, risk factor, target leverage, fixed profit per added quantity, fixed amount per quantity, fixed risk, profit risk, target margin, and Kelly stake. It SHALL expose only the inputs relevant to the selected mode and apply the mode's quantity, cap, and rounding rules to the chronological events.

#### Scenario: User configured capital mode
- **WHEN** the user selects a mode other than backtest already calculated and changes its valid inputs
- **THEN** Strategy Report SHALL recompute compound trade detail, equity, drawdown, summary, and period tables from those settings

#### Scenario: Invalid capital inputs
- **WHEN** a denominator or other required mode input is zero, negative, or absent
- **THEN** Strategy Report SHALL reject the calculation with a field specific error rather than return non finite metrics

### Requirement: Respect capital management already calculated during backtesting
In backtest already calculated mode, Strategy Report SHALL use quantities embedded in the report without applying another multiplier. It SHALL use the source initial capital when present and 100000 when absent.

#### Scenario: Source initial capital exists
- **WHEN** a report with `InitCapital`, `InitialCapital`, or `初始資金` is analyzed in this mode
- **THEN** the compound series SHALL start at that source value and use report quantities directly

#### Scenario: Source initial capital is absent
- **WHEN** a report without valid initial capital is analyzed in this mode
- **THEN** the compound series SHALL start at 100000 and use report quantities directly

#### Scenario: Range starts after first transaction
- **WHEN** the user starts the date range after earlier transactions
- **THEN** Strategy Report SHALL replay earlier events to calculate the range start capital and open positions before showing filtered results

### Requirement: Match reference calculations
The Web report's supported metric definitions SHALL be documented, and fixture tests SHALL compare the numerical summary, trade detail, annual/monthly/weekly/daily totals, and drawdown to expectations derived from C# StrategyReport source and paired format examples within explicit tolerances. Desktop output SHALL be compared when it becomes available; until then parity claims SHALL state the validation limit.

#### Scenario: SRP and SEA parity fixture
- **WHEN** equivalent `.srp` and `.sea` reference fixtures are analyzed with the same settings
- **THEN** both Web results SHALL agree with each other and the recorded source-derived expectations within the recorded tolerances

### Requirement: Export browser friendly reports
Strategy Report SHALL allow the user to download displayed detail and period tables as CSV and print the current summary and charts with a readable browser print layout.

#### Scenario: Export selected range
- **WHEN** the user exports after changing settings or date range
- **THEN** the CSV and print view SHALL represent the currently displayed calculation and identify its source report and settings

### Requirement: Match Visual Portfolio's Web presentation
Strategy Report SHALL use Visual Portfolio's gray-blue background, white bordered panels, teal accent, compact form controls, and sidebar/content layout without an introductory banner.

#### Scenario: Open the authenticated Strategy Report workspace
- **WHEN** a signed-in user opens the page at desktop or narrow viewport width
- **THEN** import controls and the report area SHALL be visible without an introductory banner in a responsive layout consistent with Visual Portfolio

### Requirement: Optional independent Buy and Hold reference
Strategy Report SHALL offer a Visual Portfolio styled Buy&Hold settings button after the date range and before capital settings, followed by the reference name or 無. The dialog SHALL offer 無, 股票, and 期貨, amount in ten-thousands, code, and futures leverage, without a date field. Its confirmation button SHALL read 設定. The reference SHALL use its own capital and leverage and SHALL be invariant under every strategy capital management mode.

#### Scenario: Automatic reference dates
- **WHEN** a reference is enabled
- **THEN** its start SHALL use the specified range start, else the report start, else the first trade date; its end SHALL use the specified end, else report end or last event date
- **AND** the first available quote on or after the start SHALL define the purchase price

#### Scenario: Reference persistence and disabling
- **WHEN** the owner applies Buy&Hold settings or selects 無
- **THEN** the report's config.json SHALL persist the setting, and copying SHALL preserve it under the new report ID
- **AND** non-owner changes SHALL affect only the current calculation

#### Scenario: Compare capital modes
- **WHEN** strategy mode, capital, quantity, or risk parameters change while reference settings and dates remain fixed
- **THEN** the reference series SHALL remain identical; simple curves SHALL show reference profit and compound curves SHALL show its own equity

#### Scenario: Unavailable reference data
- **WHEN** the provider fails or no prices exist for the requested range
- **THEN** the strategy report SHALL remain available with a visible reference error and no fabricated reference curve

### Requirement: Desktop report tab labels and Visual Portfolio summary layout
Strategy Report SHALL use the tabs 單口策略績效, 複合投資績效, 單口獲利曲線, 單口交易明細, 複合投資明細, 逐年獲利分佈, 複合資金曲線. Summary cards, labels, responsive columns, MDD table, Annual Profits and Month Profits tables SHALL match Visual Portfolio's presentation.

#### Scenario: Navigate and recalculate
- **WHEN** users select a report tab and change capital settings
- **THEN** that tab SHALL remain selected while its results update automatically
- **AND** simple and compound tabs SHALL show their respective calculations
