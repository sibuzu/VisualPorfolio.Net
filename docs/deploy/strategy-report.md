# Strategy Report deployment

The new site has its own source under `strategy-report/` and its own `strategy-report-frontend` and `strategy-report-backend` containers. It uses Visual Portfolio's existing accounts for login and mounts only root `data/reports/` for original report files and analysis settings. It does not mount Visual Portfolio's `data/db/`, `data/projects/`, or `data-beta/`. Strategy Report asks `visualportfolio-backend` to validate credentials and sessions over `sibuzu-net`. The same user ID and password work in both sites. Each hostname has its own login cookie, so a user signs in separately on each site.

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

During local development, the backend stores the performance index (IDs, names, owners, importance, source metadata, and timestamps) in `strategy-report/data/performances.db`. Original uploads are in the repository's root `data/reports/SR-XXXXXX/source.srp` or `source.sea`; capital management and date range settings live beside them in `config.json`. That JSON contains analysis settings only and is the authoritative source for subsequent calculations. Set `STRATEGY_REPORT_DATA_DIR` and `STRATEGY_REPORT_REPORTS_DIR` to change those paths. This data is separate from Visual Portfolio's databases.

## Containers

The existing Docker network `sibuzu-net` and `visualportfolio-backend` service must be running. If this is a new host, create the network once with `docker network create sibuzu-net` and start Visual Portfolio first. From the repository root:

```bash
docker compose -f docker/strategy-report/docker-compose.yml config --quiet
docker compose -f docker/strategy-report/docker-compose.yml up -d --build
./scripts/smoke-strategy-report.sh
```

The smoke script checks the homepage, health endpoint, and unauthenticated access by default. To also test `.srp` and `.sea` imports plus invalid-upload rejection, supply an existing non-guest Visual Portfolio account through `STRATEGY_REPORT_USER_ID` and `STRATEGY_REPORT_PASSWORD` in the shell environment. Do not put credentials on the command line or commit them to the repository.

The frontend binds to `127.0.0.1:8088` by default for local verification. Set `STRATEGY_REPORT_BIND=127.0.0.1:<port>` if that port is taken. The tunnel reaches `strategy-report-frontend:80` over `sibuzu-net`; it does not need the host port.

The backend stores original uploads in the repository's root `data/reports/SR-XXXXXX/`, bind mounted at `/app/data/reports/`. The named Docker volume `strategy-report-data` holds `/app/data/performances.db`, Strategy Report's independent performance index. This database is not mounted at the host's `data/db/` and does not share Visual Portfolio's `projects.db`; only account authentication is shared through Visual Portfolio's API. Back up **both** `data/reports/` and the named volume together; the database points to the files by performance ID. `docker compose down` preserves them. `down -v` deletes the database, even though the bind mounted report files remain. Original uploads with identical bytes resolve to the same file-derived `SR-` ID. A copy gets a fresh random `SR-` ID and its own source file and `config.json`; the optional “副本” suffix is only part of the display name. On startup, the backend backs up an older database as `performances.db.before-config-json`, exports each record’s saved analysis settings to its `config.json`, validates the files, and removes the obsolete SQLite settings column. IDs, owners, names, importance, and timestamps remain in the database. Interrupted exports can resume without replacing completed settings files. Legacy report BLOBs are also moved into these directories. Settings writes use atomic file replacement within a serialized storage operation; non-owner calculations leave the saved settings unchanged. When upgrading from an earlier Docker deployment that kept reports in the volume, copy its `/app/data/reports/` contents to root `data/reports/` before enabling the bind mount.

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

To revert to a Strategy Report backend from before per-report JSON settings, stop the stack and restore a matching pre-upgrade database and report-directory backup. `performances.db.before-config-json` preserves the database at the settings migration boundary; it does not include later edits.
