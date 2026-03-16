from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import init_db
from backend.routers.auth import router as auth_router
from backend.routers.analysis import router as analysis_router
from backend.routers.files import router as files_router
from backend.routers.pfo import router as pfo_router
from backend.routers.projects import router as projects_router
from backend.services.auth import init_users_db
from backend.services.cleanup import cleanup_loop, cleanup_stale_projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_users_db()
    cleanup_stale_projects()

    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(cleanup_loop(stop_event))

    app.state.stop_event = stop_event
    app.state.cleanup_task = cleanup_task
    try:
        yield
    finally:
        stop_event.set()
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="VisualPortfolio.Net API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:65173",
        "http://127.0.0.1:65173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"^https?://([a-zA-Z0-9.-]+)(:\d+)?$",
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(files_router)
app.include_router(analysis_router)
app.include_router(pfo_router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
