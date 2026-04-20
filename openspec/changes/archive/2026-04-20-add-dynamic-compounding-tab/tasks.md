## 1. Backend Contract and Simulation

- [x] 1.1 Extend analysis options to accept `dynamic_compounding` config with defaults and normalization.
- [x] 1.2 Return `dynamic_compounding.weekly` and `dynamic_compounding.monthly` payloads in analysis response.
- [x] 1.3 Implement switching rules (threshold add mode, rollback to initial, recovery to add mode) with next-period activation.
- [x] 1.4 Implement capped trading capital using `max_multiple * initial_capital * initial_ratio` and `reach_max_multiple_date`.
- [x] 1.5 Output result metrics including net values, multiple, CAGR, MDD metrics, rollback count, and scale-reach date.

## 2. MDD and Curve Calculation Standardization

- [x] 2.1 Define MDD(%) as max pointwise drawdown ratio using prior peak at each sampled point.
- [x] 2.2 Compute dynamic curve and MDD from floating net value path.
- [x] 2.3 Change sampling standard to weekly checkpoints (not daily or per-trade output points).
- [x] 2.4 Align monthly mode curve output and MDD computation to the same weekly sampling standard.
- [x] 2.5 Add backend unit tests for switching, cap enforcement, scale-reach date, and weekly-sampled MDD behavior.

## 3. Frontend Tab, Controls, and Visualization

- [x] 3.1 Add main tab `動態複利` in project view and mount dynamic compounding panel.
- [x] 3.2 Implement parameter cards, inline editing, and help button layout/wording updates.
- [x] 3.3 Display all amount fields in `萬` with integer formatting and update help text units.
- [x] 3.4 Render result table in comparison layout: rows as metrics, columns as weekly/monthly modes.
- [x] 3.5 Render `Dynamic MDD Equity Curve` with aligned weekly-sampled curves and ECharts legend styling.

## 4. State, Persistence, and Access Behavior

- [x] 4.1 Add dynamic compounding config defaults in portfolio store and include save/restore flow.
- [x] 4.2 Trigger immediate re-analysis on parameter edit without explicit apply button.
- [x] 4.3 Allow read-only projects to edit parameters for recalculation without persisting DB changes.
- [ ] 4.4 Verify production route behavior and API auth path for analysis regression tests in CI/local env.
