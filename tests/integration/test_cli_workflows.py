"""Integration coverage for primary CLI workflows."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from data_extract.cli.app import app

pytestmark = [pytest.mark.P0, pytest.mark.integration, pytest.mark.cli]


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


def test_process_command_generates_json_output(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "sample.txt", "one two three four five six")
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
            "--chunk-size",
            "3",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output

    output_file = output_dir / "sample.json"
    assert output_file.exists()
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["metadata"]["chunk_count"] == 2


def test_extract_command_supports_single_file_output_override(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "extract.txt", "extract command integration")
    output_file = tmp_path / "custom" / "extract-output.json"

    result = cli_runner.invoke(
        app,
        [
            "extract",
            str(input_file),
            "--output",
            str(output_file),
            "--format",
            "json",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()


def test_batch_command_respects_pattern_filter(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    source_dir = tmp_path / "batch"
    _write_text(source_dir / "first.txt", "first")
    _write_text(source_dir / "second.txt", "second")
    _write_text(source_dir / "ignored.md", "ignored")
    output_dir = tmp_path / "batch-output"

    result = cli_runner.invoke(
        app,
        [
            "batch",
            str(source_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
            "--pattern",
            "*.txt",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in output_dir.glob("*.json")) == ["first.json", "second.json"]


def test_validate_command_reports_supported_files(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    source_dir = tmp_path / "validate"
    _write_text(source_dir / "valid-a.txt", "a")
    _write_text(source_dir / "valid-b.txt", "b")

    result = cli_runner.invoke(app, ["validate", str(source_dir), "--recursive"])

    assert result.exit_code == 0
    assert "files valid" in result.output.lower()
