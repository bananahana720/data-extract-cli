"""Unit tests for current Typer CLI behavior."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner

import data_extract.services as services
from data_extract import __version__
from data_extract.cli.base import app
from data_extract.cli.exit_codes import EXIT_CONFIG_ERROR, EXIT_FAILURE
from data_extract.contracts import (
    FileFailure,
    JobStatus,
    ProcessJobResult,
    ProcessedFileOutcome,
    SemanticOutcome,
)

pytestmark = [pytest.mark.P0, pytest.mark.unit, pytest.mark.cli]


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@dataclass
class _StubJobService:
    result: ProcessJobResult | None = None
    error: Exception | None = None
    calls: int = 0
    last_request: object | None = None

    def run_process(self, request, work_dir=None):  # noqa: ANN001
        self.calls += 1
        self.last_request = request
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def _build_process_result(
    tmp_path: Path,
    *,
    processed: int = 1,
    failed: int = 0,
    skipped: int = 0,
    exit_code: int = 0,
    semantic_status: str | None = None,
) -> ProcessJobResult:
    return ProcessJobResult(
        job_id="job-123",
        status=JobStatus.COMPLETED if failed == 0 else JobStatus.PARTIAL,
        total_files=processed + failed + skipped,
        processed_count=processed,
        failed_count=failed,
        skipped_count=skipped,
        output_dir=str(tmp_path / "out"),
        session_id="session-abc",
        processed_files=[
            ProcessedFileOutcome(
                path=f"/input/good-{idx}.txt",
                output_path=str(tmp_path / "out" / f"good-{idx}.json"),
                chunk_count=3,
                stage_timings_ms={"extract": 10.0, "output": 5.0},
            )
            for idx in range(processed)
        ],
        failed_files=[
            FileFailure(
                path=f"/input/bad-{idx}.txt",
                error_type="extraction",
                error_message=f"failed-{idx}",
            )
            for idx in range(failed)
        ],
        stage_totals_ms={
            "extract": 100.0,
            "normalize": 40.0,
            "chunk": 70.0,
            "semantic": 20.0,
            "output": 10.0,
        },
        request_hash="req-123",
        exit_code=exit_code,
        semantic=SemanticOutcome(status=semantic_status) if semantic_status else None,
    )


def _install_stub_job_service(
    monkeypatch: pytest.MonkeyPatch,
    *,
    result: ProcessJobResult | None = None,
    error: Exception | None = None,
) -> _StubJobService:
    stub = _StubJobService(result=result, error=error)
    monkeypatch.setattr(services, "JobService", lambda: stub)
    return stub


def test_app_help_lists_core_commands(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Data Extraction Tool" in result.output
    assert "process" in result.output
    assert "version" in result.output


def test_version_flag_and_command_show_current_version(cli_runner: CliRunner) -> None:
    flag_result = cli_runner.invoke(app, ["--version"])
    cmd_result = cli_runner.invoke(app, ["version"])
    assert flag_result.exit_code == 0
    assert cmd_result.exit_code == 0
    assert __version__ in flag_result.output
    assert __version__ in cmd_result.output
    assert "Epic 5 - Enhanced CLI UX" in cmd_result.output


@pytest.mark.parametrize(
    ("args", "expected_code", "expected_text"),
    [
        (["--format", "xml"], EXIT_CONFIG_ERROR, "Invalid format 'xml'"),
        (["--pipeline-profile", "wrong"], EXIT_CONFIG_ERROR, "Invalid pipeline profile 'wrong'"),
        (["--organize"], 1, "--organize flag requires --strategy"),
        (["--strategy", "by_document"], 1, "--strategy option requires --organize"),
        (["--organize", "--strategy", "not-real"], 1, "Invalid strategy 'not-real'"),
        (["--chunk-size", "0"], EXIT_CONFIG_ERROR, "Invalid chunk size: 0"),
        (["--semantic-report-format", "yaml"], EXIT_CONFIG_ERROR, "Invalid semantic report format"),
        (["--semantic-graph-format", "svg"], EXIT_CONFIG_ERROR, "Invalid semantic graph format"),
    ],
)
def test_process_validation_errors(
    cli_runner: CliRunner,
    args: list[str],
    expected_code: int,
    expected_text: str,
) -> None:
    result = cli_runner.invoke(app, ["process", "input", *args])
    assert result.exit_code == expected_code
    assert expected_text in result.output


def test_process_builds_request_and_prints_status(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "doc.txt").write_text("content")
    stub = _install_stub_job_service(
        monkeypatch,
        result=_build_process_result(
            tmp_path, processed=1, failed=1, skipped=2, exit_code=1, semantic_status="enabled"
        ),
    )

    args = [
        "process",
        str(input_dir),
        "--output",
        str(output_dir),
        "--format",
        "txt",
        "--include-metadata",
        "--per-chunk",
        "--organize",
        "--strategy",
        "by_document",
        "--delimiter",
        "=== CHUNK {{n}} ===",
        "--recursive",
        "--incremental",
        "--force",
        "--preset",
        "quality",
        "--semantic",
        "--semantic-report",
        "--semantic-report-format",
        "csv",
        "--semantic-export-graph",
        "--semantic-graph-format",
        "dot",
        "--semantic-duplicate-threshold",
        "0.91",
        "--semantic-related-threshold",
        "0.81",
        "--semantic-max-features",
        "1200",
        "--semantic-n-components",
        "80",
        "--semantic-min-quality",
        "0.4",
        "--pipeline-profile",
        "advanced",
        "--non-interactive",
    ]
    result = cli_runner.invoke(app, args)

    assert result.exit_code == 1
    assert stub.calls == 1
    request = stub.last_request
    expected_values = {
        "input_path": str(input_dir),
        "output_path": str(output_dir.resolve()),
        "output_format": "txt",
        "include_metadata": True,
        "per_chunk": True,
        "organize": True,
        "strategy": "by_document",
        "delimiter": "=== CHUNK {{n}} ===",
        "recursive": True,
        "incremental": True,
        "force": True,
        "preset": "quality",
        "non_interactive": True,
        "include_semantic": True,
        "semantic_report": True,
        "semantic_report_format": "csv",
        "semantic_export_graph": True,
        "semantic_graph_format": "dot",
        "semantic_max_features": 1200,
        "semantic_n_components": 80,
        "pipeline_profile": "advanced",
    }
    for key, expected in expected_values.items():
        assert getattr(request, key) == expected
    assert request.semantic_duplicate_threshold == pytest.approx(0.91)
    assert request.semantic_related_threshold == pytest.approx(0.81)
    assert request.semantic_min_quality == pytest.approx(0.4)
    assert "Processing complete!" in result.output
    assert "Error summary:" in result.output
    assert "Recovery:" in result.output


def test_process_interactive_overrides_non_interactive(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "doc.txt").write_text("content")
    stub = _install_stub_job_service(monkeypatch, result=_build_process_result(tmp_path))
    result = cli_runner.invoke(
        app,
        ["process", str(input_dir), "--interactive", "--non-interactive", "--quiet"],
    )
    assert result.exit_code == 0
    assert stub.calls == 1
    assert stub.last_request.non_interactive is False


def test_process_export_summary_to_custom_path(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    summary_path = tmp_path / "nested" / "custom-summary.json"
    input_dir.mkdir()
    (input_dir / "doc.txt").write_text("content")
    stub = _install_stub_job_service(monkeypatch, result=_build_process_result(tmp_path))
    result = cli_runner.invoke(
        app,
        ["process", str(input_dir), "--quiet", "--export-summary-path", str(summary_path)],
    )
    assert result.exit_code == 0
    assert stub.calls == 1
    assert summary_path.exists()
    summary_data = json.loads(summary_path.read_text())
    assert summary_data["job_id"] == "job-123"
    assert summary_data["processed_count"] == 1


def test_process_file_not_found_maps_to_config_error(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stub_job_service(monkeypatch, error=FileNotFoundError("source not found"))
    result = cli_runner.invoke(app, ["process", "missing-input"])
    assert result.exit_code == EXIT_CONFIG_ERROR
    assert "Configuration error:" in result.output


def test_process_unexpected_exception_maps_to_failure_exit(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stub_job_service(monkeypatch, error=RuntimeError("boom"))
    result = cli_runner.invoke(app, ["process", "input"])
    assert result.exit_code == EXIT_FAILURE
    assert "Processing failed:" in result.output
