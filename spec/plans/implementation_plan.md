# VisualPortfolio.Net — Implementation Plan

## Goal
Build a web version of the existing C# WinForm `VisualPortfolio` app in `ref_source/`, with equivalent core behavior for project management, SRP/XRP parsing, portfolio analytics, and chart/table visualization.

## Stack
| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + Pinia + ECharts |
| Backend | Python 3.11+ + FastAPI |
| Database | SQLite (`data/db/projects.db`) |
| Storage | Local filesystem (`data/projects/{project-id}/`) |

## Spec Traceability (Requirements 1-8)
| Req | Requirement | Implementation |
|---|---|---|
| 1 | Port WinForm features from `ref_source/` | Port parser/calculation logic from C# service by service; reproduce UI panels as Vue tabs |
| 2 | Frontend uses Vue + ECharts; upload SRP/XRP XML | Vue workspace with upload flow, strategy manager, ECharts for equity/monthly visuals |
| 3 | Backend uses Python + FastAPI | FastAPI routers for projects/files/analysis/pfo |
| 4 | SQLite table with project fields | `projects` table includes `project_id`, `user_id`, `project_name`, `shared`, `create_time`, `access_time` |
| 5 | Guest UUID + LocalStorage + create/list projects | Frontend generates UUIDv4 on first load, stores in LocalStorage, passes as `guest_id` |
| 6 | Access rules by owner/shared | API authorization: owner edit, shared non-owner read-only, private non-owner denied |
| 7 | Project directory `data/projects/{project-id}` | Create directory at project creation; store uploads and `.pfo` there |
| 8 | Update access time and delete inactive >72h | Touch `access_time` on edit/view; periodic cleanup removes DB record + directory |

## Data Model
Table: `projects`
- `project_id` TEXT PRIMARY KEY, format: `VP[A-Z]{2}-[A-Z]{4}`
- `user_id` TEXT NOT NULL (Guest UUID)
- `project_name` TEXT NOT NULL
- `shared` INTEGER NOT NULL DEFAULT 0
- `create_time` TEXT NOT NULL (UTC ISO8601)
- `access_time` TEXT NOT NULL (UTC ISO8601)

Notes:
- Spec names fields with hyphens; DB uses snake_case columns for SQLite compatibility.
- API request/response can expose either style, but internal model uses snake_case.

## Backend Plan
### 1. Project and auth foundation
Files:
- `backend/main.py`
- `backend/db/database.py`
- `backend/models/project.py`
- `backend/routers/projects.py`
- `backend/services/project_access.py`

Work:
- Initialize DB and auto-create `projects` table.
- Implement project ID generator (`VP[A-Z]{2}-[A-Z]{4}` with collision check).
- Implement endpoints:
  - `GET /projects?guest_id=...`
  - `POST /projects`
  - `GET /projects/{project_id}`
  - `PATCH /projects/{project_id}`
  - `DELETE /projects/{project_id}`
- Enforce rules:
  - `owner`: read/write
  - `shared non-owner`: read-only
  - `private non-owner`: 403
- On project create: mkdir `data/projects/{project_id}`.
- On any successful read/write access: update `access_time`.

### 2. File upload and storage
Files:
- `backend/routers/files.py`
- `backend/services/storage.py`

Work:
- Endpoints:
  - `GET /projects/{id}/files`
  - `POST /projects/{id}/files` (only `.srp`/`.xrp`)
  - `DELETE /projects/{id}/files/{filename}`
- Save files under `data/projects/{project_id}/`.
- Validate file extension and basic XML readability.

### 3. Parser + analytics port from C#
Files:
- `backend/services/parser.py`
- `backend/services/portfolio.py`
- `backend/services/summary_report.py`
- `backend/services/commission.py`
- `backend/services/diversity.py`
- `backend/services/win_loss.py`
- `backend/routers/analysis.py`

Work:
- Port SRP/XRP parsing logic from WinForm code in `ref_source/`.
- Port trade merge, date filtering, weighted equity composition.
- Port summary/mdd/sharpe/sortino/sqn/win-loss/commission/diversity calculations.
- Endpoint:
  - `POST /projects/{id}/analysis` returns all panel data in one payload.

### 4. PFO interoperability
Files:
- `backend/routers/pfo.py`
- `backend/services/pfo.py`

Work:
- Endpoints:
  - `GET /projects/{id}/pfo`
  - `PUT /projects/{id}/pfo`
- Preserve WinForm-compatible XML schema.
- Store file references as project-relative paths.

### 5. 72-hour cleanup job
Files:
- `backend/services/cleanup.py`
- `backend/main.py`

Work:
- On startup: run one cleanup pass.
- Schedule periodic cleanup (hourly).
- Delete project where `access_time < now - 72h`.
- Delete DB row and `data/projects/{project_id}/` recursively.

## Frontend Plan
### 1. App skeleton and guest identity
Files:
- `frontend/src/main.js`
- `frontend/src/App.vue`
- `frontend/src/router/index.js`
- `frontend/src/api/index.js`

Work:
- On app load, read `localStorage.guest_uuid`.
- If missing, generate UUIDv4 and persist.
- Attach `guest_id` to API requests.

### 2. Home and project management
Files:
- `frontend/src/views/HomeView.vue`
- `frontend/src/stores/project.js`

Work:
- Show project list via `GET /projects`.
- Create project dialog (`POST /projects`).
- Rename/share toggle/delete actions (`PATCH`/`DELETE`).

### 3. Project workspace
Files:
- `frontend/src/views/ProjectView.vue`
- `frontend/src/components/EquityManager.vue`
- `frontend/src/components/*Panel.vue`
- `frontend/src/stores/portfolio.js`

Work:
- Left sidebar: uploaded files + active strategies + contract/weight/color/order/date controls.
- Right area tabs:
  - Summary
  - Equity Curve (ECharts)
  - Monthly Bar (ECharts)
  - Position Analysis
  - Win/Loss
  - Commission
  - Diversity
- Trigger re-analysis when settings change.

### 4. Read-only UX for shared projects
Work:
- If non-owner + shared project: disable edit actions (upload/delete/rename/reorder/save).
- Keep charts/tables viewable.

## API Contract (MVP)
### Projects
- `GET /projects?guest_id=UUID`
- `POST /projects` body: `{ "guest_id": "...", "project_name": "..." }`
- `GET /projects/{project_id}?guest_id=UUID`
- `PATCH /projects/{project_id}` body: `{ "guest_id": "...", "project_name": "...", "shared": true }`
- `DELETE /projects/{project_id}` body or query carries `guest_id`

### Files
- `GET /projects/{project_id}/files?guest_id=UUID`
- `POST /projects/{project_id}/files` multipart + `guest_id`
- `DELETE /projects/{project_id}/files/{filename}?guest_id=UUID`

### Analysis
- `POST /projects/{project_id}/analysis` with equities/date/options + `guest_id`
- Response includes: `summary`, `equity_curve`, `monthly`, `position_analysis`, `win_loss`, `commission`, `diversity`, `mdd_markers`

### PFO
- `GET /projects/{project_id}/pfo?guest_id=UUID`
- `PUT /projects/{project_id}/pfo` + `guest_id`

## Implementation Order
1. Backend project CRUD + access control + directory creation
2. Frontend Home page + guest UUID flow
3. File upload/list/delete
4. SRP/XRP parser and trade model
5. Portfolio + summary engine
6. Remaining calculation modules (commission/diversity/win-loss)
7. Analysis endpoint integration with all panels
8. PFO save/load interoperability
9. 72-hour cleanup scheduler + hardening
10. End-to-end verification and bug fixes

## Verification Plan
### Backend automated tests (`backend/tests`)
- `test_projects_api.py`: guest-based create/list/get/patch/delete + access policy
- `test_files_api.py`: upload/list/delete and extension checks
- `test_parser.py`: parse sample SRP/XRP from `ref_result/project`
- `test_analysis_api.py`: analysis response schema and key metrics sanity
- `test_cleanup.py`: stale project purge for `>72h`

### Frontend manual checks
1. First visit creates `guest_uuid` in LocalStorage.
2. Creating project creates DB row and `data/projects/{project_id}` directory.
3. Upload `.srp/.xrp` succeeds; files appear in list.
4. All analysis tabs render with non-empty data for sample files.
5. Shared project opened by non-owner is view-only.
6. Private project opened by non-owner returns 403.
7. Accessing project updates `access_time`.
8. Setting stale `access_time` (older than 72h) and running cleanup deletes DB row + files.

## Definition of Done
- All 8 spec requirements are implemented and mapped to tested behavior.
- Core calculations are validated against sample outputs from `ref_result/` within acceptable tolerance.
- No unauthorized edit path exists for non-owner users.
- Inactive project cleanup works for both DB and filesystem.
