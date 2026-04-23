# Beta Deployment and Release Gate

## 1. Purpose

This document defines the beta deployment baseline for `visualporforlio-beta.sibuzu.com` and the mandatory gate before production release.

## 2. Beta Environment Isolation

- Beta frontend host: `visualporforlio-beta.sibuzu.com`
- Beta API host: `api-visualporforlio-beta.sibuzu.com`
- Beta compose path: `docker/visual-portfolio-beta/docker-compose.yml`
- Beta data root: `data-beta` (must not use production `data`)

## 3. Deployment Steps

1. Prepare beta data directory:

```bash
export APP_UID=$(id -u)
export APP_GID=$(id -g)
./scripts/prepare-beta-data-dir.sh ./data-beta
```

2. Configure runtime variables and start stack:

```bash
export BETA_DATA_ROOT=../../data-beta
docker compose -f docker/visual-portfolio-beta/docker-compose.yml up -d --build
```

3. Configure tunnel/ingress using:

- `docker/visual-portfolio-beta/cloudflared-ingress.example.yml`

## 4. Validation Gate (Required Before Production)

1. Run smoke checks:

```bash
scripts/release-beta-gate.sh
```

2. Complete manual checklist:

- `docs/deploy/checklists/beta-validation.md`

3. Promotion rule:

- If smoke checks fail OR any checklist blocker remains, production deployment is forbidden.

## 5. Rollback Plan (Beta)

1. Stop beta stack:

```bash
docker compose -f docker/visual-portfolio-beta/docker-compose.yml down
```

2. Restore prior beta image tags/config (if version rollback is required).
3. Revert beta tunnel/ingress routing to previous known-good config.
4. Re-run smoke checks to confirm rollback state is healthy.

## 6. Data Retention and Cleanup

- Frequency: weekly cleanup (or after each large beta campaign)
- Owner: release on-duty engineer
- Method:
  1. Export any artifacts needed for debugging.
  2. Stop beta stack.
  3. Clean stale beta project data under `data-beta` only.
  4. Start beta stack and run smoke checks.
- Strict rule: never clean production `data` during beta cleanup operations.
