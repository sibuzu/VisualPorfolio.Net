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
The Web report's supported metric definitions SHALL be documented, and fixture tests SHALL compare the numerical summary, trade detail, annual/monthly/weekly/daily totals, and drawdown to C# StrategyReport output within explicit tolerances.

#### Scenario: SRP and SEA parity fixture
- **WHEN** equivalent `.srp` and `.sea` reference fixtures are analyzed with the same settings
- **THEN** both Web results SHALL agree with each other and the C# reference values within the recorded tolerances

### Requirement: Export browser friendly reports
Strategy Report SHALL allow the user to download displayed detail and period tables as CSV and print the current summary and charts with a readable browser print layout.

#### Scenario: Export selected range
- **WHEN** the user exports after changing settings or date range
- **THEN** the CSV and print view SHALL represent the currently displayed calculation and identify its source report and settings
