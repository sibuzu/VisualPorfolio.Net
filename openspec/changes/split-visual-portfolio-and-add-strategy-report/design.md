## Context

Visual Portfolio currently uses root `backend/` (FastAPI) and `frontend/` (Vue/Vite); production and beta Compose files build both from the repository root and bind root `data/` or `data-beta/`. This app only needs a directory move. The C# application under `/home/jack/git/hft/src/Utilities/StrategyReport/` is the functional source for the new Web app: it contains separate simple/compound detail and summary views, annual/month/week/day tables, charts, and ten capital management modes. `/home/jack/git/sea_spec/examples/srp/` contains paired `.srp` and SEA project examples useful for parity checks.

The requested public hostname is `strategyreport.sibuzu.com`. Its live DNS and tunnel configuration are outside this repository; the repository can supply container and ingress definitions and deployment checks.

## Goals / Non-Goals

**Goals:**

- Move the existing Visual Portfolio app under `visual-portfolio/` with only path/build configuration changes, preserving its implementation, URLs, API semantics, database files, and production/beta container identities.
- Deliver a separate Strategy Report site for `.srp` and `.sea` with the C# application's report concepts, adapted to a responsive browser layout.
- Establish a normalized, metadata preserving import model and deterministic report calculations with fixture comparisons to C# results.
- Make production deployment and rollback possible without moving Visual Portfolio's runtime data.

**Non-Goals:**

- Add features to Visual Portfolio, change its calculations, or extract its parser into a shared package.
- Rewrite the C# desktop application or duplicate its dockable window layout and RDLC implementation.
- Add `.pfo`, `.gsea`, `.xrp`, or directory uploads in this change; the new import boundary can be extended later.
- Combine the two apps' project databases or saved report state. Strategy Report reuses Visual Portfolio's existing account credentials through its authentication API, stores metadata in its own `data/db/reporsts.db`, and stores original reports in root `data/reports/`.
- Change live DNS or tunnel settings without access to the deployment account.

## Decisions

### Repository and imports

Use `visual-portfolio/backend/` and `visual-portfolio/frontend/` for the moved app, and `strategy-report/backend/` and `strategy-report/frontend/` for the new app. Keep root `docker/`, `data/`, `data-beta/`, `ref_result/`, `docs/`, and `openspec/`. Each app gets its own dependency manifests and test commands. Update Visual Portfolio Dockerfiles, `.gitignore`, scripts, fixture paths, and developer documentation only where the move changes paths. Retain the current `backend.*` Python import path inside the Visual Portfolio container and tests by using `visual-portfolio/` as its application root; do not alter its parser, report calculations, API, or database schema.

Alternative considered: move every root directory under `visual-portfolio/`. This would also move persistent data and deployment documents and increase production migration risk without improving code separation.

### Independent Strategy Report parser and calculations

Implement `.srp`/`.sea` decoding inside `strategy-report/backend/`, using C# StrategyReport and `sea_spec` as the behavior and format references. Its normalized model contains source format, strategy metadata, settings, ordered trade events, quantities, prices, timestamps, symbols, point value, and initial capital when present. Compute all Strategy Report summaries and capital management views from those events. Leave Visual Portfolio's parser and report calculations untouched.

Alternative considered: extract Visual Portfolio's parser into a shared package. That would change the existing app beyond the requested move and make Strategy Report dependent on portfolio specific trade conversion. Existing Visual Portfolio code can be read as a reference, but the new app does not import it.

### Web interaction and report contract

Use a separate Vue app and FastAPI API. After login, the user sees a Visual Portfolio style performance management page. The user selects one `.srp` or `.sea` file, optionally names the performance, and opens its saved report. The saved source can be reopened and recalculated after changing date range and capital management inputs. Map the C# docked forms into tabs/sections: summary, equity curves, annual/monthly/weekly/daily tables, trade detail, and capital management. Support CSV for tabular data and browser print/PDF styling; leave native `.srp`/`.sea` output for later unless parity testing reveals it is essential.

Use Visual Portfolio's existing visual language for the Strategy Report Web page: its gray-blue background, white bordered panels, teal accent, compact controls, and sidebar/content workspace. Keep the applications independent in code and deployment. The login screen uses Visual Portfolio's centered card. After login, report controls and results are visible without an introductory banner.

Saved performances use Strategy Report's own SQLite database at root `data/db/reporsts.db`, bind mounted into the container, with globally unique IDs and an authenticated owner per record. Original file bytes live in the repository's root `data/reports/SR-XXXXXX/source.srp` or `source.sea`, mounted into the Strategy Report container; SQLite holds the performance index: names, owners, importance, source metadata, and timestamps. Each report directory’s `config.json` holds capital management and date range settings. Database transactions serialize storage operations, and settings files are replaced atomically. This is a separate subdirectory from Visual Portfolio's project and database files. Uploaded `SR-` IDs use six uppercase base-26 letters derived from SHA-256 of the original bytes; copies use six random uppercase letters and a separate directory. Reuploading identical bytes opens the existing record, while a shortened-ID collision with different bytes is rejected. The first start after the storage upgrade backs up the old database, migrates its settings into per-report `config.json`, and removes the old settings column after validating the exported files. Any legacy SQLite BLOBs also move into report directories. All authenticated users can view a known performance or an important performance and recalculate with temporary settings. Only the owner may persist settings or edit metadata. The original one-request `/api/report` calculation remains available without saving. Neither path modifies Visual Portfolio's project or database files. The API enforces upload and decompression limits, rejects unsafe ZIP members, and returns clear validation errors. The deployment imposes request size and abuse limits.

Strategy Report presents the same login and sign-up flow as Visual Portfolio. Its backend sends credentials to Visual Portfolio's existing authentication API over the internal Docker network, then issues host-only cookies on `strategyreport.sibuzu.com` containing the returned signed session values. Every report request validates those cookies through Visual Portfolio's `/auth/me`. The sites therefore share user IDs and passwords while each hostname maintains its own login session. Strategy Report does not read or write `users.db`; account validation remains delegated to the existing API. Visual Portfolio application code remains unchanged.

Alternative considered: mount Visual Portfolio's `users.db` and token secret in Strategy Report. Delegating authentication to the existing API keeps account storage and token verification in one place. Saved performances are owned within Strategy Report and never appear as Visual Portfolio projects.

### Capital management parity

Implement the C# `ClsCapitalManage` modes and `FormCompoundDetail` event based calculations behind explicit, typed settings. Include the `回測時已計算` mode: use quantities already in the report without scaling; derive initial capital from `InitCapital`, `InitialCapital`, or `初始資金`, and use 100000 when absent, as documented in the C# StrategyReport TODO. For other modes, apply user settings, maximum quantity, and the C# rounding rules. Preserve range start capital by replaying earlier events when a date filter starts after the first trade. Derive summary and drawdown figures from the same detail series shown in the UI.

The C# defaults and report fields are the parity baseline, but compare numerical outputs against paired `.srp`/`.sea` fixtures before considering a mode complete. Document deliberate Web presentation changes separately from numerical differences.

### Routing and deploy

Put Strategy Report Dockerfiles and Compose under `docker/strategy-report/`, using the existing `sibuzu-net` network and distinct container names. The frontend nginx serves the SPA and proxies `/api/` to the Strategy Report backend, so the public site uses one origin: `https://strategyreport.sibuzu.com/`. Provide an ingress example mapping that hostname to the frontend container and a smoke test for home, API health, and an example import. Existing Visual Portfolio production and beta ingress remain unchanged.

Alternative considered: expose a second public API hostname. A same-origin proxy simplifies browser configuration and CORS with no required public API hostname.

## Risks / Trade-offs

- [Path migration breaks Visual Portfolio builds/tests] → Migrate imports and Compose contexts together; run existing backend tests, frontend build, and production/beta Compose config checks before adding new features.
- [Strategy Report's new parser differs from C# results] → Compare paired `.srp`/`.sea` fixtures and C# golden outputs; do not change Visual Portfolio's parser to make them match.
- [C# capital calculations have hidden edge cases] → Inventory every mode and parameter, then compare trade detail, equity, MDD, and period totals with C# golden outputs for flat, losing, overlapping, and date filtered trades.
- [Untrusted SEA ZIP consumes excessive resources or escapes paths] → Inspect archive entries without extraction, enforce compressed/uncompressed size and entry count limits, and reject malformed or unsafe members.
- [Public upload endpoint is abused or leaks report data] → Require authentication before multipart parsing, restrict request size, enforce user ownership on saved records, avoid logging report contents, and set deployment rate controls before exposing the hostname.
- [Saved reports are lost during redeployment] → Bind mount root `data/reports/` with original sources and `config.json`, keep metadata in root `data/db/reporsts.db`, and document joint backup and rollback behavior.
- [Shared account service is unavailable] → Return a service error for login and protected report requests; keep health checks independent of the account service.
- [DNS/tunnel work is unavailable from this workspace] → Commit a tested ingress example and deployment checklist; verify the live route only once the operator applies it.

## Migration Plan

1. Record baseline test/build and current Compose output. Move Visual Portfolio source with `git mv`, update paths and docs, and verify production and beta containers still mount their existing data roots.
2. Implement Strategy Report's own `.srp`/`.sea` importer and API, then its UI in vertical slices: import/metadata, simple report, capital management and compound report, tables/charts/exports. Validate each slice with C# and paired format fixture parity.
3. Add Strategy Report Compose, nginx proxy, health and smoke checks. Deploy new containers independently. Configure tunnel/DNS route to the new frontend and verify HTTPS and upload behavior.
4. Rollback: remove the new hostname route and stop only Strategy Report containers. If the Visual Portfolio source path migration causes a regression, redeploy the prior Visual Portfolio images/commit against the unchanged `data/` and `data-beta/` mounts.

## Open Questions

- Which exact C# report fields and capital modes are release critical beyond the requested `.srp`/`.sea` import? This design plans all visible modes and core report sections; the parity inventory will identify unsupported edge cases before launch.
- Who controls the Cloudflare tunnel and DNS record for `strategyreport.sibuzu.com`? The code can prepare and test the route definition; going live needs that operator's action.

### Buy&Hold and report presentation

A nullable `buy_hold` object in CalculationSettings stores product, code, amount_wan and futures leverage in the existing per-report config.json. A separate calculation accepts only these fields and the effective date range, never strategy sizing parameters. FinMind quotes are cached in a bounded hourly in-memory cache. Stock references reinvest cash dividends on ex-dates, apply stock dividends and recognize large integer split ratios using Visual Portfolio's price-ratio heuristic. Futures references use the nearest monthly daytime contract, fixed initial exposure, and roll at the prior session's prices so contract spreads are not counted as returns. Missing rollover quotes produce a reference error. No benchmark source files or Visual Portfolio projects are created.

The benchmark response carries its own equity and profit series. Time axes align it with strategy event times; the simple chart shows profit and the compound chart shows equity. The seven desktop tabs replace the former section selector and Web-specific tabs. SummaryPanel reproduces Visual Portfolio's card labels and styles with existing StrategyReport metrics; period MDD is calculated within each period. The report help panel retains source parameters and browser printing.
