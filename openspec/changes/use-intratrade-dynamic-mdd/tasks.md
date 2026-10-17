## 1. Intratrade MDD Calculation

- [x] 1.1 Move MDD amount, percentage, and date tracking to every trade-level floating-equity update.
- [x] 1.2 Keep weekly curve sampling intact and report curve drawdown relative to the intratrade peak.

## 2. Verification

- [x] 2.1 Update dynamic-compounding tests to require same-week highs and lows in MDD for weekly and monthly modes.
- [x] 2.2 Run the dynamic-compounding test suite and validate the affected OpenSpec change.
