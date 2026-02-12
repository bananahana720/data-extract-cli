"""Health endpoint router."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from data_extract.api.state import runtime

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health(detailed: bool = Query(default=False)) -> dict[str, Any]:
    """Return health and readiness signal for local runtime."""
    readiness = runtime.readiness_report
    status = readiness.get("status", "unknown")
    payload: dict[str, Any] = {
        "status": status,
        "ready": bool(readiness.get("ready", False)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if detailed:
        payload["workers"] = runtime.worker_count
        payload["queue_backlog"] = runtime.queue_backlog
        payload["recovery"] = runtime.recovery_stats
        payload["readiness"] = readiness
    return payload
