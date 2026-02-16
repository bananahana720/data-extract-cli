"""FastAPI application for local web UI/backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from data_extract.api.readiness import evaluate_runtime_readiness
from data_extract.api.routers.auth import (
    API_KEY_ENV,
    SESSION_SECRET_ENV,
    has_valid_session_cookie,
)
from data_extract.api.routers.auth import (
    router as auth_router,
)
from data_extract.api.routers.config import router as config_router
from data_extract.api.routers.health import router as health_router
from data_extract.api.routers.jobs import router as jobs_router
from data_extract.api.routers.sessions import router as sessions_router
from data_extract.api.state import runtime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UI_DIST = PROJECT_ROOT / "ui" / "dist"
REMOTE_BIND_ENV = "DATA_EXTRACT_API_REMOTE_BIND"
REQUIRE_SESSION_SECRET_REMOTE_ENV = "DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE"


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _remote_security_errors() -> list[str]:
    if not _env_flag_enabled(REMOTE_BIND_ENV, default=False):
        return []

    errors: list[str] = []
    require_session_secret = _env_flag_enabled(REQUIRE_SESSION_SECRET_REMOTE_ENV, default=True)

    if not os.environ.get(API_KEY_ENV, "").strip():
        errors.append(f"{API_KEY_ENV} is required when {REMOTE_BIND_ENV}=1.")
    if require_session_secret and not os.environ.get(SESSION_SECRET_ENV, "").strip():
        errors.append(
            f"{SESSION_SECRET_ENV} is required when {REMOTE_BIND_ENV}=1 "
            f"unless {REQUIRE_SESSION_SECRET_REMOTE_ENV}=0."
        )
    return errors


def startup_event() -> None:
    """Initialize persistence and worker runtime."""
    security_errors = _remote_security_errors()
    if security_errors:
        raise RuntimeError("Remote bind security policy violation: " + " ".join(security_errors))
    runtime.start()
    runtime.set_readiness_report(evaluate_runtime_readiness())


def shutdown_event() -> None:
    """Stop worker runtime."""
    runtime.stop()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    startup_event()
    try:
        yield
    finally:
        shutdown_event()


app = FastAPI(title="Data Extract UI API", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(config_router)
app.include_router(jobs_router)
app.include_router(sessions_router)


@app.middleware("http")
async def api_key_guard(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Protect API/docs endpoints when DATA_EXTRACT_API_KEY is configured."""
    configured_key = os.environ.get(API_KEY_ENV, "").strip()
    if not configured_key:
        return await call_next(request)

    path = request.url.path
    protected_prefixes = ("/api/", "/docs", "/redoc", "/openapi")
    if path.startswith(protected_prefixes):
        if path.startswith("/api/v1/auth/session"):
            return await call_next(request)

        provided_key = request.headers.get("x-api-key", "")
        if provided_key == configured_key or has_valid_session_cookie(request):
            return await call_next(request)

        if provided_key != configured_key:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


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
