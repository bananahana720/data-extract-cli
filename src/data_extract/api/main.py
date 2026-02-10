"""FastAPI application for local web UI/backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from data_extract.api.routers.config import router as config_router
from data_extract.api.routers.health import router as health_router
from data_extract.api.routers.jobs import router as jobs_router
from data_extract.api.routers.sessions import router as sessions_router
from data_extract.api.state import runtime

app = FastAPI(title="Data Extract UI API", version="1.0.0")
app.include_router(health_router)
app.include_router(config_router)
app.include_router(jobs_router)
app.include_router(sessions_router)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UI_DIST = PROJECT_ROOT / "ui" / "dist"


@app.on_event("startup")
def startup_event() -> None:
    """Initialize persistence and worker runtime."""
    runtime.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    """Stop worker runtime."""
    runtime.stop()


if UI_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(UI_DIST / "assets")), name="assets")


@app.get("/", response_model=None)
def serve_root() -> object:
    """Serve built frontend if available, else runtime hint."""
    index_path = UI_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {
            "message": "UI build not found. Run: cd ui && npm install && npm run build",
            "api_docs": "/docs",
        }
    )


@app.get("/{path:path}", response_model=None)
def serve_spa(path: str) -> object:
    """Serve SPA routes while leaving API paths to API routers."""
    if (
        path.startswith("api/")
        or path.startswith("docs")
        or path.startswith("redoc")
        or path.startswith("openapi")
    ):
        raise HTTPException(status_code=404, detail="Not found")

    index_path = UI_DIST / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI build not found")
    return FileResponse(index_path)
