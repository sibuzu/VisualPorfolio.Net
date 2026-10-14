## 1. Baseline and reference inventory

- [x] 1.1 Record the current Visual Portfolio backend test, frontend build, production Compose config, and beta Compose config results.
- [x] 1.2 Inventory C# StrategyReport's visible summary fields, detail columns, period tables, chart series, ten capital modes, defaults, date range behavior, and save/print behavior in a parity matrix.
- [x] 1.3 Select paired `.srp` and `.sea` fixtures from `sea_spec/examples/srp/`; record source-derived expected values for normal, losing, overlapping, and filtered trades, the C# source version, and the current desktop-output validation limit.

## 2. Visual Portfolio source relocation

- [x] 2.1 Move root `backend/` and `frontend/` into `visual-portfolio/` with Git history preserving moves and update the app's local development and test commands.
- [x] 2.2 Update Visual Portfolio production and beta Dockerfiles and Compose build references while retaining current service/container names and root `data/` and `data-beta/` mounts.
- [x] 2.3 Update root ignore patterns, scripts, fixture paths, links, and deployment/developer documentation affected by the source move.
- [x] 2.4 Run the existing Visual Portfolio backend tests and frontend build; compare API fixtures and production/beta Compose output against the baseline.

## 3. Strategy Report import foundation

- [x] 3.1 Define Strategy Report's own typed metadata, settings, events, and trade models from C# StrategyReport and `sea_spec` references.
- [x] 3.2 Implement `.srp` XML decoding and initial capital metadata parsing inside `strategy-report/backend/`, including `InitCapital`, `InitialCapital`, `初始資金`, separators, and `萬`.
- [x] 3.3 Implement `.sea` archive, TOML, and JSONL decoding inside `strategy-report/backend/` with bounded ZIP reads and explicit invalid file errors.
- [x] 3.4 Add paired `.srp`/`.sea` normalization tests and malformed/oversized/unsafe archive tests.

## 4. Strategy Report backend

- [x] 4.1 Scaffold `strategy-report/backend/` with independent dependencies, health endpoint, file upload/calculation API, request validation, and size limits.
- [x] 4.2 Build the simple trade profit series, summary metrics, drawdown, and annual/monthly/weekly/daily aggregates from the normalized events; compare reference fixtures.
- [x] 4.3 Implement backtest already calculated mode with source quantities, source initial capital or 100000 fallback, and range start replay of prior events.
- [x] 4.4 Implement fixed quantity, fixed profit per added quantity, and fixed amount per quantity modes with C# defaults, caps, and rounding.
- [x] 4.5 Implement risk factor, target leverage, fixed risk, and profit risk modes with field specific validation and C# quantity rules.
- [x] 4.6 Implement target margin and Kelly stake modes with field specific validation and C# quantity rules.
- [x] 4.7 Build compound detail, summary, equity, drawdown, and period aggregates from one consistent post-management series; compare every capital mode to reference fixtures.
- [x] 4.8 Verify import isolation, temporary file cleanup, non finite input rejection, and concurrent request separation.
- [x] 4.9 Delegate account signup, login, and session validation to Visual Portfolio's authentication API; require a valid non-guest session before parsing report uploads.

## 5. Strategy Report frontend

- [x] 5.1 Scaffold `strategy-report/frontend/` as an independent Vue/Vite app with an import screen, validation feedback, and source metadata display.
- [x] 5.2 Add responsive summary, simple/compound equity and drawdown charts, and annual/monthly/weekly/daily report sections.
- [x] 5.3 Add chronological trade detail, date range selection, and consistent loading/error/empty states.
- [x] 5.4 Add capital management mode controls that show relevant fields and recalculate the report; preserve the selected file in the browser for a new request without server persistence.
- [x] 5.5 Add CSV downloads for the displayed detail and period tables plus a readable browser print/PDF layout labeled with source and settings.
- [x] 5.6 Build the frontend and verify key flows at desktop and narrow viewport widths, including keyboard navigation and chart/table readability.
- [x] 5.7 Remove the introductory banner and align Strategy Report's responsive CSS and sidebar/content layout with Visual Portfolio.
- [x] 5.8 Add a Visual Portfolio style login/sign-up screen and Strategy Report hostname session/logout controls.

## 6. Containers and hostname route

- [x] 6.1 Add `docker/strategy-report/` backend/frontend Dockerfiles, Compose stack, nginx `/api/` proxy, and health checks with unique service names on `sibuzu-net`.
- [x] 6.2 Add a Cloudflare ingress example for `strategyreport.sibuzu.com`, request limits, deployment steps, and rollback steps that leave Visual Portfolio data untouched.
- [x] 6.3 Add and run local smoke checks for homepage, API health, valid `.srp`/`.sea` import, and invalid upload rejection.
- [x] 6.3a Update smoke checks for login protection and optional authenticated import using an existing Visual Portfolio account.
- [ ] 6.4 Have the operator apply the live DNS/tunnel route, then verify HTTPS homepage and API upload through `strategyreport.sibuzu.com` before declaring the public domain live.

## 7. Final acceptance

- [x] 7.1 Re-run Visual Portfolio regression tests, frontend build, and production/beta Compose checks; verify its application code changed only as required by source relocation.
- [x] 7.2 Run the full Strategy Report parity matrix and record any intentional presentation differences or numerical exceptions.
- [x] 7.3 Document the final repository layout, both applications' local commands, data ownership, supported input formats, and operational limits.
