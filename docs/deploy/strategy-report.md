# Strategy Report deployment

The new site has its own source under `strategy-report/` and its own `strategy-report-frontend` and `strategy-report-backend` containers. It uses Visual Portfolio's existing accounts for login and bind mounts root `data/reports/` for report files/settings and root `data/db/` for its independent `reporsts.db`. Visual Portfolio continues to use `users.db` and `projects.db` in that directory; Strategy Report authenticates through its API. Strategy Report asks `visualportfolio-backend` to validate credentials and sessions over `sibuzu-net`. The same user ID and password work in both sites. Each hostname has its own login cookie, so a user signs in separately on each site.

## Local run

From the repository root, install the backend's `strategy-report/backend/requirements.txt` in a Python environment, then run:

```bash
VISUAL_PORTFOLIO_AUTH_URL=http://127.0.0.1:8000 PYTHONPATH=strategy-report/backend uvicorn strategy_report.main:app --host 127.0.0.1 --port 8001
```

In another shell:

```bash
cd strategy-report/frontend
npm ci
npm run dev
```

Run Visual Portfolio's backend on port 8000 for local login, or set `VISUAL_PORTFOLIO_AUTH_URL` to its reachable internal URL. Vite proxies `/api/` to port 8001. Run backend tests with `PYTHONPATH=strategy-report/backend python -m pytest strategy-report/backend/tests -q` from the repository root.

During local development, the backend stores the performance index (IDs, names, owners, importance, source metadata, and timestamps) in `data/db/reporsts.db`. Original uploads are in the repository's root `data/reports/SR-XXXXXX/source.srp` or `source.sea`; capital management and date range settings live beside them in `config.json`. That JSON contains analysis settings only and is the authoritative source for subsequent calculations. Set `STRATEGY_REPORT_DATA_DIR` and `STRATEGY_REPORT_REPORTS_DIR` to change those paths. This data is separate from Visual Portfolio's databases.

## Containers

The existing Docker network `sibuzu-net` and `visualportfolio-backend` service must be running. If this is a new host, create the network once with `docker network create sibuzu-net` and start Visual Portfolio first. From the repository root:

```bash
mkdir -p data/db data/reports
env UID="$(id -u)" GID="$(id -g)" docker compose -f docker/strategy-report/docker-compose.yml config --quiet
env UID="$(id -u)" GID="$(id -g)" docker compose -f docker/strategy-report/docker-compose.yml up -d --build
./scripts/smoke-strategy-report.sh
```

The smoke script checks the homepage, health endpoint, and unauthenticated access by default. To also test `.srp` and `.sea` imports plus invalid-upload rejection, supply an existing non-guest Visual Portfolio account through `STRATEGY_REPORT_USER_ID` and `STRATEGY_REPORT_PASSWORD` in the shell environment. Do not put credentials on the command line or commit them to the repository.

The frontend binds to `127.0.0.1:8088` by default for local verification. Set `STRATEGY_REPORT_BIND=127.0.0.1:<port>` if that port is taken. The tunnel reaches `strategy-report-frontend:80` over `sibuzu-net`; it does not need the host port.

The backend bind mounts host `data/db/` at `/app/data/db/` and stores its independent index at `/app/data/db/reporsts.db` (the filename intentionally follows the requested spelling). Report source files and `config.json` remain in host `data/reports/SR-XXXXXX/`, mounted at `/app/data/reports/`. The container runs with the host UID/GID, defaulting to `1000:1000`, so both paths remain writable from the host. For a different UID/GID, pass them through the Compose environment as shown above.

On an upgrade, the previous `strategy-report-data` volume is mounted read-only at `/app/legacy-data/`. If `reporsts.db` does not yet exist, the backend uses SQLite backup to copy `STRATEGY_REPORT_LEGACY_DB` (set to `/app/legacy-data/performances.db` in Compose) into the new location. The old database remains untouched, and an existing target is never overwritten. Local development also recognizes the old `strategy-report/data/performances.db`. Before restarting an older deployment that created report files as UID 10001, change ownership of `data/reports/` to the host UID/GID used by the container. The old volume can be retained as a migration backup; current reads and writes use the host database.

Back up `data/db/reporsts.db` and `data/reports/` together. Visual Portfolio's `users.db` and `projects.db` remain separate files. `docker compose down` preserves the host files. Original uploads with identical bytes resolve to the same file-derived `SR-` ID. A copy gets a fresh random `SR-` ID and its own source file and `config.json`; the optional “副本” suffix is only part of the display name.

When migrating an older schema, the backend backs up the database as `reporsts.db.before-config-json`, exports its saved analysis settings to each report's `config.json`, validates them, and removes the obsolete SQLite settings column. IDs, owners, names, importance, and timestamps remain in the database. Interrupted exports can resume without replacing completed settings files. Legacy report BLOBs are also moved into the report directories. Settings writes use atomic file replacement within a serialized storage operation; non-owner calculations leave saved settings unchanged.

Signed-in users can open a performance by its URL and see important performances on the management page. Only its owner can rename, mark important, delete, or persist capital management settings. A different signed-in viewer can change settings and recalculate for the current view, then copy the performance to become the owner of a separate copy. The download action returns a ZIP containing `source.srp` or `source.sea` plus `performance.json`.

Add the hostname rule from `docker/strategy-report/cloudflared-ingress.example.yml` before the existing tunnel's catch-all rule, and route the DNS name `strategyreport.sibuzu.com` to that tunnel. This repository contains an example, not the live Cloudflare tunnel credentials or account configuration. After the operator applies the route:

```bash
STRATEGY_REPORT_URL=https://strategyreport.sibuzu.com ./scripts/smoke-strategy-report.sh
```

Only report the hostname as live after HTTPS homepage, health endpoint, login with an existing Visual Portfolio account, `.srp` and `.sea` import, and invalid-upload rejection pass through the public URL. The report endpoint requires login; the health endpoint and login page are public.

Uploads are limited to 20 MiB by the API and 21 MiB by nginx. SEA archives have limits on entry count and uncompressed size. Creating a performance saves the original report in root `data/reports/`; opening or recalculating it reads that saved source. The legacy `/api/report` endpoint still processes an uploaded report for one request without saving it. Avoid putting sensitive report content into logs.

## Rollback

Remove the Strategy Report hostname rule from the tunnel, then stop only the new stack:

```bash
docker compose -f docker/strategy-report/docker-compose.yml down
```

Visual Portfolio containers and their `data/` and `data-beta/` directories remain in place.

To revert to a Strategy Report backend from before per-report JSON settings, stop the stack and restore a matching pre-upgrade database and report-directory backup. `reporsts.db.before-config-json` (or the older `performances.db.before-config-json` backup) preserves the database at the settings migration boundary; it does not include later edits.

## Buy&Hold reference

The button below the date range opens the Visual Portfolio style settings dialog. Select 無 to disable the reference, 股票 for a stock/ETF, or 期貨 for a futures contract. Set amount in 萬, code (for example 0050 or TX), and futures leverage, then press 設定. No manual benchmark date is needed: the selected range start takes priority over the source report start, falling back to the first trade. The selected range end, source report end, or last event limits quotes. Holidays advance the purchase to the first available trading day.

The reference uses its own amount and leverage; strategy capital management never rescales it. Stock cash dividends are reinvested on ex-dates; stock dividends and large integer price splits are accounted for (split detection follows Visual Portfolio's heuristic, not a full corporate-action database). Futures use daytime nearest-month prices, fixed initial exposure, and prior-session rollover prices to exclude contract spreads. Both omit commissions and taxes. A provider error or missing rollover quote shows a message while retaining the strategy report.

行情來源：[FinMind 股票行情](https://finmind.github.io/tutor/TaiwanMarket/Technical/)、[配息欄位](https://finmind.github.io/tutor/TaiwanMarket/Fundamental/)、[期貨行情](https://finmind.github.io/tutor/TaiwanMarket/Derivative/)。The backend caches successful quote requests for the current hour. Optionally provide `FINMIND_TOKEN` through the shell or Compose `--env-file`; the token stays in the backend environment. Anonymous access remains subject to FinMind's limits.

`config.json` stores `buy_hold: null` for 無, or for example `{"product_type":"股票","code":"0050","amount_wan":"100","leverage":"5"}`. Existing configs default to 無. Owner edits persist; viewer edits remain temporary; copies inherit the saved reference settings. No extra report directories or database columns are needed.

The report uses the desktop tab labels: 單口績效、單口曲線、單口明細、複合績效、複合曲線、複合明細、逐年獲利. Summary cards and tables follow Visual Portfolio. The question-mark control contains report help, source parameters, and print/PDF.

Date fields initially show the input's first and last event dates, even with 指定 unchecked. Existing saved dates take precedence. `date_range_enabled` stores the checkbox separately, so unchecking restores the full calculation without discarding the entered dates. Only owner calculations persist these values in `config.json`; viewers cannot change them. Older settings without the flag retain their previous date-filter behavior.

Performance workspace URLs use `/reports/SR-XXXXXX`, including navigation and copied links. The former `/performances/` page path has no compatibility route or redirect.
