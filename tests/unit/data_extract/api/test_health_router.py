from __future__ import annotations

import os

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

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
    assert "queue_backlog" in payload
    assert "recovery" in payload
    assert "readiness" in payload
