# Implementation baseline

Recorded 2026-10-14 UTC against Visual Portfolio commit `326d79e31a014828f09092f04c142436b22af48f`, before moving its source tree.

| Check | Command | Result |
| --- | --- | --- |
| Backend | `.venv/bin/python -m pytest backend/tests -q` | 45 passed, 5 failed (50 total, 2.23 s). All five failures are 401 responses because the older test helpers create projects without logging in. Failing files: `test_analysis_snapshots.py` (2), `test_integration_e2e.py` (2), `test_projects_api.py` (1). |
| Frontend | `cd frontend && npm run build` | Passed; Vite built 665 modules. Existing warning: one 1,264 kB JS chunk exceeds 500 kB. |
| Production Compose | `docker compose -f docker/visual-portfolio/docker-compose.yml config --quiet` | Passed. |
| Beta Compose | `docker compose -f docker/visual-portfolio-beta/docker-compose.yml config --quiet` | Passed. |

Relocation acceptance compares against this baseline. The five pre-existing authentication test failures are not part of the Strategy Report work or a Visual Portfolio feature change.

After moving the source and updating paths, `PYTHONPATH=visual-portfolio .venv/bin/python -m pytest visual-portfolio/backend/tests -q` also had 45 passes and the same five 401 failures. `npm run build` from `visual-portfolio/frontend/` produced the same asset hashes and size warning. Both production and beta Compose config checks passed.
