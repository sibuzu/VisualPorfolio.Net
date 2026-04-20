# dynamic-compounding-analysis Specification

## Purpose
TBD - created by archiving change add-dynamic-compounding-tab. Update Purpose after archive.
## Requirements
### Requirement: Dynamic Compounding Analysis Contract
The system SHALL accept an optional `dynamic_compounding` configuration in analysis options and SHALL return `dynamic_compounding.weekly` and `dynamic_compounding.monthly` results in the analysis response.

#### Scenario: Request without explicit dynamic compounding config
- **WHEN** client calls analysis API without `dynamic_compounding`
- **THEN** system SHALL use default values:
  - `initial_capital=80,000,000`
  - `initial_ratio=0.10`
  - `add_threshold_profit=100,000,000`
  - `add_ratio=0.15`
  - `rollback_amount=20,000,000`
  - `max_multiple=10`
- **THEN** response SHALL include both `weekly` and `monthly` result objects.

#### Scenario: Response schema for each mode
- **WHEN** analysis API returns dynamic compounding output
- **THEN** each mode SHALL include:
  - `initial_net_value`
  - `final_net_value`
  - `profit_multiple`
  - `cagr_pct`
  - `mdd_pct`
  - `mdd_amount`
  - `rollback_adjust_count`
  - `reach_max_multiple_date`
  - `curve`

### Requirement: Dynamic Compounding Switching and Cap Rules
The system SHALL apply dynamic compounding mode transitions using strict greater-than comparisons and period-next-step switching.

#### Scenario: Enter add mode after threshold
- **WHEN** cumulative profit becomes greater than `add_threshold_profit` while in initial mode
- **THEN** system SHALL switch to add mode on the next period.

#### Scenario: Roll back to initial mode on drawdown
- **WHEN** system is in add mode and drawdown from prior peak becomes greater than `rollback_amount`
- **THEN** system SHALL switch to initial mode on the next period
- **THEN** system SHALL increment `rollback_adjust_count`.

#### Scenario: Re-enter add mode after recovery
- **WHEN** system has rolled back to initial mode and net value later makes a new high above the rollback reference peak
- **THEN** system SHALL switch back to add mode on the next period.

#### Scenario: Cap trading capital by max multiple
- **WHEN** computed trading capital exceeds `max_multiple * initial_capital * initial_ratio`
- **THEN** system SHALL clamp trading capital to that cap
- **THEN** system SHALL set `reach_max_multiple_date` to the first period end date where cap was reached
- **THEN** system SHALL return `未達成` when never reached.

### Requirement: Weekly-Sampled Floating Equity Standard for MDD and Curve
The system SHALL calculate MDD and output equity curve using floating net value sampled at weekly checkpoints for both weekly and monthly modes.

#### Scenario: Use weekly checkpoints instead of daily or per-trade output
- **WHEN** simulation processes floating net value updates
- **THEN** system SHALL aggregate output curve points to one point per ISO week
- **THEN** the point date SHALL be the last available trade date in that week.

#### Scenario: Monthly mode aligned to weekly sampling
- **WHEN** monthly rebalance simulation generates floating net values
- **THEN** curve output SHALL still use weekly checkpoints
- **THEN** MDD for monthly mode SHALL be computed from this weekly-sampled floating equity path.

#### Scenario: MDD percentage definition
- **WHEN** MDD is computed from sampled equity points
- **THEN** system SHALL compute drawdown percentage at each sampled point as `(peak_before_point - equity_point) / peak_before_point`
- **THEN** reported `mdd_pct` SHALL be the maximum of those pointwise percentages.

### Requirement: Dynamic Compounding UI and Read-Only Recalculate Behavior
The frontend SHALL provide a dedicated dynamic compounding tab with editable parameters, help text, result table, and chart; read-only projects SHALL still allow local edits and recomputation.

#### Scenario: Read-only project recalculation
- **WHEN** project is view-only and user edits dynamic compounding parameters
- **THEN** frontend SHALL trigger analysis recomputation with edited values
- **THEN** frontend SHALL NOT persist edited values to DB
- **THEN** page refresh SHALL restore persisted project defaults.

#### Scenario: Result table and chart consistency
- **WHEN** analysis response includes weekly and monthly dynamic compounding results
- **THEN** frontend SHALL render a comparison table with both modes
- **THEN** chart SHALL plot weekly-sampled floating equity curves for both modes on the same time axis.

