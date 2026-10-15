# VisualPorfolio.Net

This repository contains two independent Web applications:

| Application | Source | Docker stack | Persistent data |
| --- | --- | --- | --- |
| Visual Portfolio | [`visual-portfolio/`](visual-portfolio/) | `docker/visual-portfolio/` and `docker/visual-portfolio-beta/` | Root `data/` and `data-beta/` |
| Strategy Report | [`strategy-report/`](strategy-report/) | `docker/strategy-report/` | `data/reports/<ID>/` for source/configuration; `data/db/reporsts.db` for the performance index |

Visual Portfolio's source was moved under `visual-portfolio/` without changing its application features. Its local commands are in [`visual-portfolio/README.md`](visual-portfolio/README.md).

Strategy Report is a separate Vue and Python Web implementation of the C# StrategyReport utility. It uses the existing Visual Portfolio user ID and password for login, saves uploaded `.srp` and `.sea` reports under stable file-derived `SR-` IDs, and gives each copied performance a new random `SR-` ID. Original files and capital management/date range settings (`config.json`) live in the repository's root `data/reports/<ID>/` directories. Strategy Report keeps names, owners, importance, and source metadata in its separate `data/db/reporsts.db`. Owners' capital settings persist; other signed-in viewers can change settings for their current view. It offers CSV and browser print output. Local commands, deployment, hostname routing, limits, and rollback are in [`docs/deploy/strategy-report.md`](docs/deploy/strategy-report.md).

The Strategy Report calculation checks use C# source formulas and paired files from `sea_spec/examples`. A desktop-generated C# report is not available in this environment, so numerical equivalence to a running C# binary remains unverified. See [`openspec/changes/split-visual-portfolio-and-add-strategy-report/parity-matrix.md`](openspec/changes/split-visual-portfolio-and-add-strategy-report/parity-matrix.md).
