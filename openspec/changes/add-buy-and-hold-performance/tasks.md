## 1. Backend API and Data Service

- [x] 1.1 Add Buy&Hold request/response models for date, amount, product type, code, optional leverage, generated filename, and display name.
- [x] 1.2 Add a project-scoped owner-only Buy&Hold router endpoint and register it in the FastAPI app.
- [x] 1.3 Implement FinMind stock price and dividend fetching behind a service boundary with clear empty-data errors.
- [x] 1.4 Implement FinMind futures price fetching and deterministic rollover selection behind the same service boundary.
- [x] 1.5 Implement daily floating equity calculation with fractional entry positions for stock dividend reinvestment and futures leveraged rollover series.
- [x] 1.6 Serialize generated Buy&Hold results as `.sea` files with `strategy.toml` metadata and daily event data.
- [x] 1.7 Sanitize generated Buy&Hold filenames and overwrite the existing same-name Buy&Hold file.

## 2. Frontend Workflow

- [x] 2.1 Add a two-row strategy portfolio control area containing `+ Buy&Hold`, `+新增績效`, and `上傳專案`.
- [x] 2.2 Add the Buy&Hold dialog with title, help control, date, amount, product type, code, and conditional leverage fields.
- [x] 2.3 Keep Buy&Hold fields as textbox-style inputs and default futures leverage to `5`.
- [x] 2.4 Add API/store support for calling the Buy&Hold endpoint and surfacing loading/error states.
- [x] 2.5 After successful generation, reload project files, include the generated performance in the equity list, and refresh analysis.
- [x] 2.6 Prevent Buy&Hold creation for read-only projects.

## 3. Validation and Tests

- [x] 3.1 Add backend unit tests for generated naming, filename overwrite handling, owner-only access, and no-file-on-error behavior.
- [x] 3.2 Add backend calculation tests for stock dividend reinvestment, fractional entry positions, and futures leverage/rollover using deterministic mocked FinMind data.
- [x] 3.3 Add frontend tests or component-level checks for dialog visibility, conditional leverage input, default leverage, help text, and refresh flow.
- [x] 3.4 Run OpenSpec validation and the relevant backend/frontend test suites.
