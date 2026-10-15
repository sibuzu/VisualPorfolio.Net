# Strategy Report deployment

The new site has its own source under `strategy-report/` and its own `strategy-report-frontend` and `strategy-report-backend` containers. It uses Visual Portfolio's existing accounts for login, but never mounts root `data/` or `data-beta/`. Strategy Report asks `visualportfolio-backend` to validate credentials and sessions over `sibuzu-net`. The same user ID and password work in both sites. Each hostname has its own login cookie, so a user signs in separately on each site.

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

The backend stores saved performances in `strategy-report/data/` during local development. Each original upload is at `data/reports/SR-XXXXXX/source.srp` or `source.sea` relative to that data directory; names, owners, importance, and settings are in `data/performances.db`. Set `STRATEGY_REPORT_DATA_DIR` to another writable directory if needed. This data is separate from Visual Portfolio's databases.

## Containers

The existing Docker network `sibuzu-net` and `visualportfolio-backend` service must be running. If this is a new host, create the network once with `docker network create sibuzu-net` and start Visual Portfolio first. From the repository root:

```bash
docker compose -f docker/strategy-report/docker-compose.yml config --quiet
docker compose -f docker/strategy-report/docker-compose.yml up -d --build
./scripts/smoke-strategy-report.sh
```

The smoke script checks the homepage, health endpoint, and unauthenticated access by default. To also test `.srp` and `.sea` imports plus invalid-upload rejection, supply an existing non-guest Visual Portfolio account through `STRATEGY_REPORT_USER_ID` and `STRATEGY_REPORT_PASSWORD` in the shell environment. Do not put credentials on the command line or commit them to the repository.

The frontend binds to `127.0.0.1:8088` by default for local verification. Set `STRATEGY_REPORT_BIND=127.0.0.1:<port>` if that port is taken. The tunnel reaches `strategy-report-frontend:80` over `sibuzu-net`; it does not need the host port.

The backend stores original uploads under `/app/data/reports/SR-XXXXXX/` and metadata in `/app/data/performances.db` in the named Docker volume `strategy-report-data`. Back up this volume before host migration. `docker compose down` preserves it; do not use `down -v` unless deleting all saved Strategy Report performances is intended. Original uploads with identical bytes resolve to the same file-derived `SR-` ID. A copy gets a fresh random `SR-` ID and its own directory; the optional “副本” suffix is only part of the display name. On first start after upgrading from BLOB storage, the backend moves legacy report bytes into these directories while retaining existing IDs and metadata.

Signed-in users can open a performance by its URL and see important performances on the management page. Only its owner can rename, mark important, delete, or persist capital management settings. A different signed-in viewer can change settings and recalculate for the current view, then copy the performance to become the owner of a separate copy. The download action returns a ZIP containing `source.srp` or `source.sea` plus `performance.json`.

Add the hostname rule from `docker/strategy-report/cloudflared-ingress.example.yml` before the existing tunnel's catch-all rule, and route the DNS name `strategyreport.sibuzu.com` to that tunnel. This repository contains an example, not the live Cloudflare tunnel credentials or account configuration. After the operator applies the route:

```bash
STRATEGY_REPORT_URL=https://strategyreport.sibuzu.com ./scripts/smoke-strategy-report.sh
```

Only report the hostname as live after HTTPS homepage, health endpoint, login with an existing Visual Portfolio account, `.srp` and `.sea` import, and invalid-upload rejection pass through the public URL. The report endpoint requires login; the health endpoint and login page are public.

Uploads are limited to 20 MiB by the API and 21 MiB by nginx. SEA archives have limits on entry count and uncompressed size. Creating a performance saves the original report in Strategy Report's own volume; opening or recalculating it reads that saved source. The legacy `/api/report` endpoint still processes an uploaded report for one request without saving it. Avoid putting sensitive report content into logs.

## Rollback

Remove the Strategy Report hostname rule from the tunnel, then stop only the new stack:

```bash
docker compose -f docker/strategy-report/docker-compose.yml down
```

Visual Portfolio containers and their `data/` and `data-beta/` directories remain in place.
