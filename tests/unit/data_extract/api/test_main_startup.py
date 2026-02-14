from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import APIRouter

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")


def _router_module(module_name: str) -> types.ModuleType:
    module = types.ModuleType(module_name)
    module.router = APIRouter()
    return module


def _load_main_module(monkeypatch):
    calls = {"start": 0, "set_readiness_report": 0}

    def _start() -> None:
        calls["start"] += 1

    def _stop() -> None:
        return None

    def _set_readiness_report(_report) -> None:
        calls["set_readiness_report"] += 1

    runtime = SimpleNamespace(
        start=_start,
        stop=_stop,
        set_readiness_report=_set_readiness_report,
    )

    data_extract_package = types.ModuleType("data_extract")
    data_extract_package.__path__ = []
    api_package = types.ModuleType("data_extract.api")
    api_package.__path__ = []
    routers_package = types.ModuleType("data_extract.api.routers")
    routers_package.__path__ = []

    readiness_stub = types.ModuleType("data_extract.api.readiness")
    readiness_stub.evaluate_runtime_readiness = lambda: {
        "status": "ok",
        "ready": True,
        "errors": [],
        "warnings": [],
    }

    auth_stub = types.ModuleType("data_extract.api.routers.auth")
    auth_stub.API_KEY_ENV = "DATA_EXTRACT_API_KEY"
    auth_stub.SESSION_SECRET_ENV = "DATA_EXTRACT_API_SESSION_SECRET"
    auth_stub.has_valid_session_cookie = lambda _request: False
    auth_stub.router = APIRouter()

    state_stub = types.ModuleType("data_extract.api.state")
    state_stub.runtime = runtime

    monkeypatch.setitem(sys.modules, "data_extract", data_extract_package)
    monkeypatch.setitem(sys.modules, "data_extract.api", api_package)
    monkeypatch.setitem(sys.modules, "data_extract.api.routers", routers_package)
    monkeypatch.setitem(sys.modules, "data_extract.api.readiness", readiness_stub)
    monkeypatch.setitem(sys.modules, "data_extract.api.routers.auth", auth_stub)
    monkeypatch.setitem(
        sys.modules, "data_extract.api.routers.config", _router_module("config_router_stub")
    )
    monkeypatch.setitem(
        sys.modules, "data_extract.api.routers.health", _router_module("health_router_stub")
    )
    monkeypatch.setitem(
        sys.modules, "data_extract.api.routers.jobs", _router_module("jobs_router_stub")
    )
    monkeypatch.setitem(
        sys.modules, "data_extract.api.routers.sessions", _router_module("sessions_router_stub")
    )
    monkeypatch.setitem(sys.modules, "data_extract.api.state", state_stub)

    module_path = Path(__file__).resolve().parents[4] / "src" / "data_extract" / "api" / "main.py"
    spec = importlib.util.spec_from_file_location("data_extract_api_main_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, calls


def test_startup_fails_fast_when_remote_bind_missing_api_key(monkeypatch) -> None:
    main_module, calls = _load_main_module(monkeypatch)
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND", "1")
    monkeypatch.delenv("DATA_EXTRACT_API_KEY", raising=False)
    monkeypatch.setenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", "0")

    with pytest.raises(RuntimeError, match="DATA_EXTRACT_API_KEY"):
        main_module.startup_event()

    assert calls["start"] == 0
    assert calls["set_readiness_report"] == 0


def test_startup_fails_fast_when_remote_bind_requires_session_secret(monkeypatch) -> None:
    main_module, calls = _load_main_module(monkeypatch)
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-key")
    monkeypatch.setenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", "1")
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="DATA_EXTRACT_API_SESSION_SECRET"):
        main_module.startup_event()

    assert calls["start"] == 0
    assert calls["set_readiness_report"] == 0


def test_startup_allows_remote_bind_when_policy_requirements_met(monkeypatch) -> None:
    main_module, calls = _load_main_module(monkeypatch)
    monkeypatch.setenv("DATA_EXTRACT_API_REMOTE_BIND", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-key")
    monkeypatch.setenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", "0")
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)

    main_module.startup_event()

    assert calls["start"] == 1
    assert calls["set_readiness_report"] == 1
