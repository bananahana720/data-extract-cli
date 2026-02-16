"""Integration tests for CLI summary export and summary module outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rich import box as rich_box
from typer.testing import CliRunner

from data_extract.cli.app import app
from data_extract.cli.summary import (
    ExportFormat,
    QualityMetrics,
    SummaryReport,
    export_summary_parallel,
    render_summary_panel,
)

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.story_5_4, pytest.mark.cli]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_cli_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_EXTRACT_UI_HOME", str(tmp_path / "ui-home"))
    monkeypatch.setenv("DATA_EXTRACT_WORK_DIR", str(tmp_path / "work-dir"))


def test_process_command_exports_default_summary_file(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "summary.txt", "alpha beta gamma")
    output_dir = tmp_path / "output"

    result = cli_runner.invoke(
        app,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "json",
            "--export-summary",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output

    summary_file = output_dir / "summary.json"
    assert summary_file.exists()

    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    assert payload["processed_count"] == 1
    assert payload["failed_count"] == 0
    assert isinstance(payload["stage_totals_ms"], dict)


def test_process_command_exports_summary_to_custom_path(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "custom-summary.txt", "one two three")
    output_dir = tmp_path / "output"
    summary_path = tmp_path / "reports" / "summary-custom.json"

    result = cli_runner.invoke(
        app,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "json",
            "--export-summary-path",
            str(summary_path),
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output
    assert summary_path.exists()

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert Path(payload["output_dir"]) == output_dir.resolve()


def test_summary_module_parallel_export_generates_txt_json_html(tmp_path: Path) -> None:
    report = SummaryReport(
        files_processed=3,
        files_failed=1,
        chunks_created=7,
        errors=("sample failure",),
        quality_metrics=QualityMetrics(
            avg_quality=0.87,
            excellent_count=2,
            good_count=3,
            review_count=2,
            flagged_count=1,
            entity_count=4,
            readability_score=58.2,
            duplicate_percentage=10.0,
        ),
        timing={"extract": 20.0, "normalize": 10.0, "chunk": 15.0, "semantic": 0.0, "output": 5.0},
        config={"format": "json"},
        next_steps=("Retry failed files",),
        processing_duration_ms=50.0,
    )

    exports = export_summary_parallel(
        report,
        output_dir=tmp_path / "exports",
        formats=[ExportFormat.TXT, ExportFormat.JSON, ExportFormat.HTML],
        max_workers=2,
    )

    assert set(exports) == {ExportFormat.TXT, ExportFormat.JSON, ExportFormat.HTML}
    assert all(path.exists() for path in exports.values())

    json_payload = json.loads(exports[ExportFormat.JSON].read_text(encoding="utf-8"))
    txt_payload = exports[ExportFormat.TXT].read_text(encoding="utf-8")
    html_payload = exports[ExportFormat.HTML].read_text(encoding="utf-8")

    assert json_payload["files_processed"] == 3
    assert "PROCESSING SUMMARY REPORT" in txt_payload
    assert "<!DOCTYPE html>" in html_payload
    assert "<style>" in html_payload


def test_render_summary_panel_uses_ascii_box_when_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")

    report = SummaryReport(
        files_processed=1,
        files_failed=0,
        chunks_created=2,
        errors=(),
        quality_metrics=None,
        timing={"extract": 1.0, "normalize": 1.0, "chunk": 1.0, "semantic": 0.0, "output": 1.0},
        config={},
        next_steps=(),
    )

    panel = render_summary_panel(report)
    assert panel.box == rich_box.ASCII
