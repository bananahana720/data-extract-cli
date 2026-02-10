"""Health endpoint router."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return basic health signal for local runtime."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
