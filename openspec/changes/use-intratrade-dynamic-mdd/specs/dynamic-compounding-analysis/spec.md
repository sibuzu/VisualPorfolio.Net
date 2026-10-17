## MODIFIED Requirements

### Requirement: Weekly-Sampled Floating Equity Standard for MDD and Curve
The system SHALL calculate dynamic-compounding MDD from every floating-equity update after each trade, while outputting the equity curve at weekly checkpoints for both weekly and monthly modes.

#### Scenario: Use weekly checkpoints for curve output
- **WHEN** simulation processes floating net value updates
- **THEN** system SHALL aggregate output curve points to one point per ISO week
- **THEN** the point date SHALL be the last available trade date in that week.

#### Scenario: Monthly mode aligned to weekly curve sampling
- **WHEN** monthly rebalance simulation generates floating net values
- **THEN** curve output SHALL still use weekly checkpoints
- **THEN** MDD for monthly mode SHALL be computed from every intra-month trade-level floating-equity update rather than only the weekly curve points.

#### Scenario: MDD percentage definition
- **WHEN** MDD is computed from trade-level floating-equity updates
- **THEN** system SHALL compute drawdown percentage at each update as `(peak_before_point - equity_point) / peak_before_point`
- **THEN** reported `mdd_pct` SHALL be the maximum of those pointwise percentages.

#### Scenario: MDD amount and dates use trade-level updates
- **WHEN** a trade-level floating-equity update produces a new maximum drawdown amount or percentage
- **THEN** system SHALL update the corresponding MDD value and date from that trade-level point.

#### Scenario: Same-week high and low are included in MDD
- **WHEN** floating equity reaches a high and subsequently falls within the same ISO week
- **THEN** system SHALL include that high-to-low movement when calculating MDD even though only the week-ending point is emitted in the curve.
