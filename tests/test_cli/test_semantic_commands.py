"""Deterministic tests for semantic CLI command routing.

These tests validate semantic command dispatch and subprocess command construction
without requiring optional runtime dependencies (Typer, NumPy, scikit-learn).
"""

from __future__ import annotations

import subprocess
import sys
import types

import pytest

# The repository-level test hook skips all CLI tests when Typer is unavailable.
# Provide a minimal module shim so these deterministic routing tests are collected.
if "typer" not in sys.modules:
    sys.modules["typer"] = types.ModuleType("typer")

from data_extract.cli.models import CommandResult
from data_extract.cli.router import CommandRouter, Pipeline


@pytest.fixture
def router() -> CommandRouter:
    """Create a fresh command router."""
    return CommandRouter()


class TestSemanticDispatch:
    """Validate semantic command routing behavior."""

    def test_semantic_requires_subcommand(self, router: CommandRouter) -> None:
        result = router.execute("semantic")

        assert result.success is False
        assert result.exit_code == 1
        assert result.errors
        assert "requires a subcommand" in result.errors[0].lower()

    def test_semantic_unknown_subcommand(self, router: CommandRouter) -> None:
        result = router.execute("semantic", "unknown")

        assert result.success is False
        assert result.exit_code == 1
        assert result.errors
        assert "unknown semantic subcommand" in result.errors[0].lower()

    @pytest.mark.parametrize(
        "subcommand",
        ["analyze", "deduplicate", "cluster", "topics"],
    )
    def test_semantic_subcommand_dispatches_to_cli(
        self,
        router: CommandRouter,
        monkeypatch: pytest.MonkeyPatch,
        subcommand: str,
    ) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_run_cli_command(*args: str, **_kwargs: object) -> CommandResult:
            calls.append(args)
            return CommandResult(success=True, exit_code=0, output="ok")

        monkeypatch.setattr(router, "_run_cli_command", fake_run_cli_command)

        result = router.execute("semantic", subcommand, "./chunks", "--output", "out.json")

        assert result.success is True
        assert calls == [("semantic", subcommand, "./chunks", "--output", "out.json")]


class TestSubprocessExecution:
    """Validate subprocess invocation and error handling."""

    def test_run_cli_command_builds_expected_command(
        self,
        router: CommandRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        seen: dict[str, object] = {}

        def fake_subprocess_run(
            cmd: list[str],
            capture_output: bool,
            text: bool,
            timeout: int,
        ) -> subprocess.CompletedProcess[str]:
            seen["cmd"] = cmd
            seen["capture_output"] = capture_output
            seen["text"] = text
            seen["timeout"] = timeout
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="done", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

        result = router._run_cli_command("semantic", "topics", "./chunks")

        assert result.success is True
        assert result.exit_code == 0
        assert result.output == "done"
        assert seen["cmd"] == [
            sys.executable,
            "-m",
            "data_extract.app",
            "semantic",
            "topics",
            "./chunks",
        ]
        assert seen["capture_output"] is True
        assert seen["text"] is True
        assert seen["timeout"] == 300

    def test_run_cli_command_handles_timeout(
        self,
        router: CommandRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def raise_timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(cmd="data_extract", timeout=300)

        monkeypatch.setattr(subprocess, "run", raise_timeout)

        result = router._run_cli_command("semantic", "analyze", "./chunks")

        assert result.success is False
        assert result.exit_code == 124
        assert result.errors
        assert "timed out" in result.errors[0].lower()

    def test_run_cli_command_handles_file_not_found(
        self,
        router: CommandRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def raise_not_found(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            raise FileNotFoundError("missing file")

        monkeypatch.setattr(subprocess, "run", raise_not_found)

        result = router._run_cli_command("semantic", "cluster", "./missing.json")

        assert result.success is False
        assert result.exit_code == 1
        assert result.errors
        assert "file not found" in result.errors[0].lower()


class TestPipelineComposition:
    """Validate semantic-related pipeline composition behavior."""

    def test_pipeline_stops_after_first_failure(self) -> None:
        calls: list[str] = []
        router = CommandRouter()

        def succeed(*_args: str, **_kwargs: object) -> CommandResult:
            calls.append("success")
            return CommandResult(success=True, exit_code=0, output="ok")

        def fail(*_args: str, **_kwargs: object) -> CommandResult:
            calls.append("fail")
            return CommandResult(success=False, exit_code=2, output="", errors=["boom"])

        def should_not_run(*_args: str, **_kwargs: object) -> CommandResult:
            calls.append("late")
            return CommandResult(success=True, exit_code=0, output="late")

        router.register("first", succeed)
        router.register("second", fail)
        router.register("third", should_not_run)

        pipeline = Pipeline(
            commands=[("first",), ("second",), ("third",)],
            router=router,
        )

        result = pipeline.run()

        assert calls == ["success", "fail"]
        assert result.success is False
        assert result.exit_code == 2
        assert result.errors == ["boom"]

    def test_pipeline_empty_commands_returns_error(self) -> None:
        router = CommandRouter()
        pipeline = Pipeline(commands=[], router=router)

        result = pipeline.run()

        assert result.success is False
        assert result.exit_code == 1
        assert result.errors == ["Empty pipeline"]
