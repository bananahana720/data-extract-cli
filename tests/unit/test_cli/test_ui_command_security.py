from __future__ import annotations

import os
import sys
import types
from pathlib import Path

from typer.testing import CliRunner

from data_extract.cli.base import create_app


def _stub_ui_dependencies(monkeypatch, tmp_path: Path) -> None:
    app_home = tmp_path / "ui-home"
    app_home.mkdir(parents=True, exist_ok=True)

    api_package = types.ModuleType("data_extract.api")
    api_package.__path__ = []

    database_stub = types.ModuleType("data_extract.api.database")
    database_stub.APP_HOME = app_home
    database_stub.DB_PATH = app_home / "app.db"

    readiness_stub = types.ModuleType("data_extract.api.readiness")
    readiness_stub.evaluate_runtime_readiness = lambda: {
        "status": "ok",
        "ready": True,
        "errors": [],
        "warnings": [],
        "checks": {},
        "ocr_readiness": {
            "status": "ok",
            "available": True,
            "strict": False,
            "message": "OCR available",
        },
        "checked_at": "2026-02-14T00:00:00Z",
    }

    monkeypatch.setitem(sys.modules, "data_extract.api", api_package)
    monkeypatch.setitem(sys.modules, "data_extract.api.database", database_stub)
    monkeypatch.setitem(sys.modules, "data_extract.api.readiness", readiness_stub)


def test_ui_remote_bind_without_allow_remote_is_blocked(monkeypatch, tmp_path) -> None:
    _stub_ui_dependencies(monkeypatch, tmp_path)
    app = create_app()
    runner = CliRunner()

    result = runner.invoke(app, ["ui", "--host", "0.0.0.0", "--check"])

    assert result.exit_code == 1
    assert "Refusing non-local host binding without --allow-remote" in result.output
    assert os.environ.get("DATA_EXTRACT_API_REMOTE_BIND") == "1"


def test_ui_allow_remote_requires_api_key_and_session_secret_by_default(
    monkeypatch, tmp_path
) -> None:
    _stub_ui_dependencies(monkeypatch, tmp_path)
    monkeypatch.delenv("DATA_EXTRACT_API_KEY", raising=False)
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)
    monkeypatch.delenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", raising=False)
    app = create_app()
    runner = CliRunner()

    result = runner.invoke(app, ["ui", "--host", "0.0.0.0", "--allow-remote", "--check"])

    assert result.exit_code == 1
    assert "DATA_EXTRACT_API_KEY is required when using --allow-remote." in result.output
    assert "DATA_EXTRACT_API_SESSION_SECRET is required when using --allow-remote" in result.output
    assert os.environ.get("DATA_EXTRACT_API_REMOTE_BIND") == "1"


def test_ui_allow_remote_can_disable_session_secret_requirement(monkeypatch, tmp_path) -> None:
    _stub_ui_dependencies(monkeypatch, tmp_path)
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-api-key")
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)
    monkeypatch.setenv("DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE", "0")
    app = create_app()
    runner = CliRunner()

    result = runner.invoke(app, ["ui", "--host", "0.0.0.0", "--allow-remote", "--check"])

    assert result.exit_code == 0
    assert "Runtime checks passed." in result.output
    assert os.environ.get("DATA_EXTRACT_API_REMOTE_BIND") == "1"


def test_ui_local_bind_sets_remote_bind_env_zero(monkeypatch, tmp_path) -> None:
    _stub_ui_dependencies(monkeypatch, tmp_path)
    monkeypatch.delenv("DATA_EXTRACT_API_KEY", raising=False)
    monkeypatch.delenv("DATA_EXTRACT_API_SESSION_SECRET", raising=False)
    app = create_app()
    runner = CliRunner()

    result = runner.invoke(app, ["ui", "--host", "127.0.0.1", "--check"])

    assert result.exit_code == 0
    assert os.environ.get("DATA_EXTRACT_API_REMOTE_BIND") == "0"
