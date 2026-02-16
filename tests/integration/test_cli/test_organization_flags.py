"""Integration tests for CLI --organize/--strategy combinations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from data_extract.cli.app import app

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.cli, pytest.mark.organization]


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


def test_cli_organize_by_document_creates_nested_output(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "document.txt", "alpha beta gamma delta")
    output_dir = tmp_path / "organized"

    result = cli_runner.invoke(
        app,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "txt",
            "--chunk-size",
            "2",
            "--organize",
            "--strategy",
            "by_document",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    created_files = [output_dir / rel_path for rel_path in manifest["files"]]

    assert manifest["strategy"] == "by_document"
    assert manifest["chunk_count"] >= 1
    assert created_files
    assert all(path.exists() for path in created_files)
    assert any(path.parent != output_dir for path in created_files)


def test_cli_organize_by_entity_routes_chunks_to_entities_folder(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
) -> None:
    input_file = _write_text(tmp_path / "entity.txt", "one two three four")
    output_dir = tmp_path / "organized-entities"

    result = cli_runner.invoke(
        app,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "txt",
            "--chunk-size",
            "2",
            "--organize",
            "--strategy",
            "by_entity",
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    created_files = [output_dir / rel_path for rel_path in manifest["files"]]

    assert manifest["strategy"] == "by_entity"
    assert (output_dir / "entities").is_dir()
    assert created_files
    assert all(path.parent.name == "entities" for path in created_files)


@pytest.mark.parametrize(
    ("args", "error_fragment"),
    [
        (
            ["--organize"],
            "requires --strategy",
        ),
        (
            ["--strategy", "by_document"],
            "requires --organize",
        ),
        (
            ["--organize", "--strategy", "not_real"],
            "invalid strategy",
        ),
    ],
)
def test_cli_organization_flag_validation_errors(
    cli_runner: CliRunner,
    tmp_path: Path,
    isolated_cli_env: None,
    args: list[str],
    error_fragment: str,
) -> None:
    input_file = _write_text(tmp_path / "invalid.txt", "sample")
    output_dir = tmp_path / "output"

    result = cli_runner.invoke(
        app,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "txt",
            *args,
        ],
    )

    assert result.exit_code == 1
    assert error_fragment in result.output.lower()
