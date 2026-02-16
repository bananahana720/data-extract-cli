from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")


def _load_health_module(monkeypatch):
    runtime = SimpleNamespace(
        worker_count=2,
        alive_workers=2,
        dead_workers=0,
        worker_restarts=0,
        queue_backlog=0,
        queue_capacity=16,
        queue_utilization=0.0,
        overload_stats={"throttle_rejections": 0},
        recovery_stats={"requeued": 0, "failed": 0},
        terminal_reconciliation_stats={"scanned": 0, "repaired": 0},
        db_lock_retry_stats={"operations": {}},
        pending_dispatch_count=3,
        artifact_sync_backlog_count=2,
        session_projection_drift_count=1,
    )

    data_extract_package = types.ModuleType("data_extract")
    data_extract_package.__path__ = []
    api_package = types.ModuleType("data_extract.api")
    api_package.__path__ = []
    routers_package = types.ModuleType("data_extract.api.routers")
    routers_package.__path__ = []

    auth_stub = types.ModuleType("data_extract.api.routers.auth")
    auth_stub.API_KEY_ENV = "DATA_EXTRACT_API_KEY"
    auth_stub.SESSION_SECRET_ENV = "DATA_EXTRACT_API_SESSION_SECRET"

    state_stub = types.ModuleType("data_extract.api.state")
    state_stub.runtime = runtime

    monkeypatch.setitem(sys.modules, "data_extract", data_extract_package)
    monkeypatch.setitem(sys.modules, "data_extract.api", api_package)
    monkeypatch.setitem(sys.modules, "data_extract.api.routers", routers_package)
    monkeypatch.setitem(sys.modules, "data_extract.api.routers.auth", auth_stub)
    monkeypatch.setitem(sys.modules, "data_extract.api.state", state_stub)

    module_path = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "data_extract"
        / "api"
        / "routers"
        / "health.py"
    )
    spec = importlib.util.spec_from_file_location("data_extract_health_router_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, runtime


def test_health_detailed_includes_runtime_snapshot(monkeypatch) -> None:
    module, runtime = _load_health_module(monkeypatch)
    runtime.readiness_report = {
        "status": "degraded",
        "ready": True,
        "errors": [],
        "warnings": ["sample warning"],
        "checks": {"sample": True},
        "ocr_readiness": {
            "status": "warning",
            "available": False,
            "strict": False,
            "message": "OCR unavailable",
        },
        "checked_at": "2026-02-11T00:00:00",
    }

    payload = module.health(detailed=True)

    assert payload["status"] == "degraded"
    assert payload["ready"] is True
    assert payload["workers"] == 2
    assert payload["alive_workers"] == 2
    assert payload["dead_workers"] == 0
    assert payload["worker_restarts"] == 0
    assert payload["queue_backlog"] == 0
    assert payload["queue_capacity"] == 16
    assert payload["queue_utilization"] == 0.0
    assert "queue_overload" in payload
    assert "db_lock_retry_stats" in payload
    assert "startup_terminal_reconciliation" in payload
    assert "recovery" in payload
    assert "readiness" in payload
    assert "security_policy" in payload
    assert "ocr_readiness" in payload
    assert payload["pending_dispatch_jobs"] == 3
    assert payload["artifact_sync_backlog"] == 2
    assert payload["session_projection_drift"] == 1
    assert "operations" in payload["db_lock_retry_stats"]


def test_health_detailed_security_policy_reflects_remote_auth_config(monkeypatch) -> None:
    module, runtime = _load_health_module(monkeypatch)
    runtime.readiness_report = {"status": "ok", "ready": True, "errors": [], "warnings": []}
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-key")
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)

    payload = module.health(detailed=True)
    policy = payload["security_policy"]

    assert policy["remote_bind"] is True
    assert policy["api_key_configured"] is True
    assert policy["session_secret_configured"] is False
    assert policy["require_session_secret_remote"] is True
    assert policy["remote_auth_ready"] is False


def test_health_detailed_security_policy_exposes_length_metrics(monkeypatch) -> None:
    module, runtime = _load_health_module(monkeypatch)
    runtime.readiness_report = {"status": "ok", "ready": True, "errors": [], "warnings": []}
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "abcdefghij")
    monkeypatch.setenv("DATA_EXTRACT_API_SESSION_SECRET", "secretvalue")
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND_MIN_API_KEY_LENGTH", "8")
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND_MIN_SESSION_SECRET_LENGTH", "16")

    payload = module.health(detailed=True)
    policy = payload["security_policy"]

    assert policy["api_key_length"] == 10
    assert policy["min_api_key_length"] == 8
    assert policy["api_key_length_compliant"] is True
    assert policy["session_secret_length"] == 11
    assert policy["min_session_secret_length"] == 16
    assert policy["session_secret_length_compliant"] is False


def test_health_detailed_includes_optional_runtime_counters(monkeypatch) -> None:
    module, runtime = _load_health_module(monkeypatch)
    runtime.readiness_report = {"status": "ok", "ready": True, "errors": [], "warnings": []}
    runtime.custom_counters = {"jobs_completed": 4}

    payload = module.health(detailed=True)

    assert payload["custom_counters"] == {"jobs_completed": 4}
