# Strategy Report deployment

The new site is independent of Visual Portfolio. Its source is under `strategy-report/`; its containers are `strategy-report-frontend` and `strategy-report-backend`. It never mounts root `data/` or `data-beta/`.

## Local run

From the repository root, install the backend's `strategy-report/backend/requirements.txt` in a Python environment, then run:

```bash
PYTHONPATH=strategy-report/backend uvicorn strategy_report.main:app --host 127.0.0.1 --port 8001
```

In another shell:

```bash
cd strategy-report/frontend
npm ci
npm run dev
```

Vite proxies `/api/` to port 8001. Run backend tests with `PYTHONPATH=strategy-report/backend python -m pytest strategy-report/backend/tests -q` from the repository root.

## Containers

The existing Docker network `sibuzu-net` must exist. If this is a new host, create it once with `docker network create sibuzu-net`. From the repository root:

```bash
docker compose -f docker/strategy-report/docker-compose.yml config --quiet
docker compose -f docker/strategy-report/docker-compose.yml up -d --build
./scripts/smoke-strategy-report.sh
```

The frontend binds to `127.0.0.1:8088` by default for local verification. Set `STRATEGY_REPORT_BIND=127.0.0.1:<port>` if that port is taken. The tunnel reaches `strategy-report-frontend:80` over `sibuzu-net`; it does not need the host port.

Add the hostname rule from `docker/strategy-report/cloudflared-ingress.example.yml` before the existing tunnel's catch-all rule, and route the DNS name `strategyreport.sibuzu.com` to that tunnel. This repository contains an example, not the live Cloudflare tunnel credentials or account configuration. After the operator applies the route:

```bash
STRATEGY_REPORT_URL=https://strategyreport.sibuzu.com ./scripts/smoke-strategy-report.sh
```

Only report the hostname as live after HTTPS homepage, health endpoint, `.srp` and `.sea` import, and invalid-upload rejection pass through the public URL. The public access policy remains an operational decision before launch.

Uploads are limited to 20 MiB by the API and 21 MiB by nginx. SEA archives have limits on entry count and uncompressed size. Reports are processed per request and are not stored as projects. Avoid putting sensitive report content into logs.

## Rollback

Remove the Strategy Report hostname rule from the tunnel, then stop only the new stack:

```bash
docker compose -f docker/strategy-report/docker-compose.yml down
```

Visual Portfolio containers and their `data/` and `data-beta/` directories remain in place.
