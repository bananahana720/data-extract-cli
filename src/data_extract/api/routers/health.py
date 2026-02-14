"""Health endpoint router."""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from data_extract.api.routers.auth import API_KEY_ENV, SESSION_SECRET_ENV
from data_extract.api.state import runtime

router = APIRouter(prefix="/api/v1", tags=["health"])
REMOTE_BIND_ENV = "DATA_EXTRACT_API_REMOTE_BIND"
REQUIRE_SESSION_SECRET_REMOTE_ENV = "DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE"

_CORE_COUNTER_ATTRS = {
    "worker_count",
    "alive_workers",
    "dead_workers",
    "worker_restarts",
    "queue_backlog",
    "queue_capacity",
    "queue_utilization",
    "overload_stats",
    "recovery_stats",
    "terminal_reconciliation_stats",
    "db_lock_retry_stats",
}


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _build_security_policy_snapshot() -> dict[str, Any]:
    remote_bind = _env_flag_enabled(REMOTE_BIND_ENV, default=False)
    require_session_secret_remote = _env_flag_enabled(
        REQUIRE_SESSION_SECRET_REMOTE_ENV,
        default=True,
    )
    api_key_configured = bool(os.environ.get(API_KEY_ENV, "").strip())
    session_secret_configured = bool(os.environ.get(SESSION_SECRET_ENV, "").strip())
    remote_auth_ready = not remote_bind or (
        api_key_configured and (session_secret_configured or not require_session_secret_remote)
    )
    return {
        "remote_bind": remote_bind,
        "remote_auth_ready": remote_auth_ready,
        "api_key_configured": api_key_configured,
        "session_secret_configured": session_secret_configured,
        "require_session_secret_remote": require_session_secret_remote,
    }


def _ocr_readiness_from_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    raw = readiness.get("ocr_readiness")
    if isinstance(raw, dict):
        return dict(raw)
    return {
        "status": "unknown",
        "available": False,
        "strict": _env_flag_enabled("DATA_EXTRACT_API_OCR_READINESS_STRICT", default=False),
        "message": "OCR readiness unavailable.",
    }


def _collect_optional_runtime_counters() -> dict[str, Any]:
    extras: dict[str, Any] = {}
    for attr_name in dir(runtime):
        if attr_name.startswith("_") or attr_name in _CORE_COUNTER_ATTRS:
            continue
        if not (attr_name.endswith("_stats") or attr_name.endswith("_counters")):
            continue

        try:
            value = getattr(runtime, attr_name)
        except Exception:
            continue

        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
            except Exception:
                continue

        if isinstance(value, Mapping):
            extras[attr_name] = dict(value)
        elif isinstance(value, (str, int, float, bool, list, tuple)):
            extras[attr_name] = value

    return extras


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
        payload["alive_workers"] = runtime.alive_workers
        payload["dead_workers"] = runtime.dead_workers
        payload["worker_restarts"] = runtime.worker_restarts
        payload["queue_backlog"] = runtime.queue_backlog
        payload["queue_capacity"] = runtime.queue_capacity
        payload["queue_utilization"] = runtime.queue_utilization
        payload["queue_overload"] = runtime.overload_stats
        payload["recovery"] = runtime.recovery_stats
        payload["startup_terminal_reconciliation"] = runtime.terminal_reconciliation_stats
        payload["db_lock_retry_stats"] = runtime.db_lock_retry_stats
        payload["pending_dispatch_jobs"] = int(getattr(runtime, "pending_dispatch_count", 0))
        payload["artifact_sync_backlog"] = int(getattr(runtime, "artifact_sync_backlog_count", 0))
        payload["session_projection_drift"] = int(
            getattr(runtime, "session_projection_drift_count", 0)
        )
        payload["security_policy"] = _build_security_policy_snapshot()
        payload["ocr_readiness"] = _ocr_readiness_from_readiness(readiness)
        payload["readiness"] = readiness
        for key, value in _collect_optional_runtime_counters().items():
            payload.setdefault(key, value)
    return payload
