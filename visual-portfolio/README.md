# Visual Portfolio

The existing Visual Portfolio backend and frontend were moved into this directory without changing their application logic. Run these commands from the repository root:

```bash
PYTHONPATH=visual-portfolio .venv/bin/python -m pytest visual-portfolio/backend/tests -q
PYTHONPATH=visual-portfolio .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Run the frontend from `visual-portfolio/frontend/`:

```bash
cd visual-portfolio/frontend
npm ci
npm run dev
```

The production and beta Compose entry points remain `docker/visual-portfolio/` and `docker/visual-portfolio-beta/`. Their persistent data directories remain at root `data/` and `data-beta/`. The root `visual-portfolio/index.html` is an older tracked development file; the Vite app uses `visual-portfolio/frontend/index.html`.
