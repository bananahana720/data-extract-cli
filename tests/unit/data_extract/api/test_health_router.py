from __future__ import annotations

import os

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from sqlalchemy.exc import OperationalError

from data_extract.api.database import with_sqlite_lock_retry
from data_extract.api.routers.health import health
from data_extract.api.state import runtime


def test_health_detailed_includes_runtime_snapshot() -> None:
    runtime.set_readiness_report(
        {
            "status": "degraded",
            "ready": True,
            "errors": [],
            "warnings": ["sample warning"],
            "checks": {"sample": True},
            "checked_at": "2026-02-11T00:00:00",
        }
    )

    payload = health(detailed=True)

    assert payload["status"] == "degraded"
    assert payload["ready"] is True
    assert "workers" in payload
    assert "alive_workers" in payload
    assert "dead_workers" in payload
    assert "worker_restarts" in payload
    assert "queue_backlog" in payload
    assert "queue_capacity" in payload
    assert "queue_utilization" in payload
    assert "queue_overload" in payload
    assert "db_lock_retry_stats" in payload
    assert "startup_terminal_reconciliation" in payload
    assert "recovery" in payload
    assert "readiness" in payload
    assert "operations" in payload["db_lock_retry_stats"]
    assert isinstance(payload["db_lock_retry_stats"]["operations"], dict)


def test_health_detailed_includes_operation_scoped_lock_stats() -> None:
    operation_name = "tests.health.lock_observability"
    attempts = {"count": 0}

    def flaky_operation() -> None:
        if attempts["count"] == 0:
            attempts["count"] += 1
            raise OperationalError(
                "database is locked",
                params=None,
                orig=Exception("database is locked"),
            )

    with_sqlite_lock_retry(
        flaky_operation,
        retries=1,
        backoff_ms=1,
        operation_name=operation_name,
        serialize_writes=False,
    )

    payload = health(detailed=True)
    operation_stats = payload["db_lock_retry_stats"]["operations"].get(operation_name)

    assert operation_stats is not None
    assert operation_stats["retries"] >= 1
    assert operation_stats["successes"] >= 1
