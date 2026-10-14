## Why

The repository currently places Visual Portfolio's application code at the root, which makes a second Web application awkward to develop and deploy. The C# StrategyReport already defines useful single strategy and capital managed reports; a separate Web edition should make those reports available from `.srp` and `.sea` files without disrupting the existing Visual Portfolio site.

## What Changes

- **BREAKING** for source paths and build commands: move the existing `backend/` and `frontend/` into `visual-portfolio/`, and update only the paths, scripts, documentation, and Docker build references needed for the move. Preserve Visual Portfolio's code behavior, URLs, API, and persistent data; add no Visual Portfolio features or shared parser refactor.
- Add an independent `strategy-report/` Web app based on the C# StrategyReport. It imports `.srp` and `.sea` and presents its single strategy and capital managed summaries, details, tables, and charts in a browser, with browser friendly report export.
- Add `docker/strategy-report/` for the new frontend and backend, including the ingress configuration needed for `https://strategyreport.sibuzu.com/`.
- Define parity fixtures and acceptance checks against C# StrategyReport, including reports whose capital management was already calculated during backtesting.

## Capabilities

### New Capabilities

- `multi-app-repository-layout`: Move only Visual Portfolio's source tree and give the new Strategy Report app its own source tree and builds.
- `strategy-report-import`: Safe upload and normalization of `.srp` and `.sea` strategy reports, including report metadata and capital management flags.
- `strategy-report-analysis`: Single strategy and capital managed summary, detail, periodic tables, and charts with C# parity rules.
- `strategy-report-deployment`: Container deployment and documented hostname routing for the Strategy Report Web app.

### Modified Capabilities

None. Existing Visual Portfolio capabilities and public behavior remain the same.

## Impact

- Code: move root `backend/` and `frontend/`; adjust their path references in tests, `docker/visual-portfolio*`, scripts, and docs; add `visual-portfolio/` and independent `strategy-report/` code. Visual Portfolio's parser and report logic are unchanged.
- APIs: new Strategy Report API; existing Visual Portfolio endpoints and domain stay stable.
- Runtime: separate Strategy Report frontend/backend containers and hostname route. Live DNS/tunnel changes require access to the existing deployment configuration.
- Reference behavior: `/home/jack/git/hft/src/Utilities/StrategyReport/` and `/home/jack/git/sea_spec/examples/`. The C# app also supports `.pfo`, `.gsea`, and directory based `strategy.toml`; those formats are outside this request's initial `.srp`/`.sea` acceptance scope.
