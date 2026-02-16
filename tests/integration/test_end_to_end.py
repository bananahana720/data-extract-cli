"""End-to-end integration tests using JobService orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.contracts import ProcessJobRequest
from data_extract.services.job_service import JobService

pytestmark = [pytest.mark.P0, pytest.mark.integration]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def isolated_runtime_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    work_dir = tmp_path / "work-dir"
    monkeypatch.setenv("DATA_EXTRACT_UI_HOME", str(tmp_path / "ui-home"))
    monkeypatch.setenv("DATA_EXTRACT_WORK_DIR", str(work_dir))
    return work_dir


def test_end_to_end_single_file_explicit_output_file(
    tmp_path: Path,
    isolated_runtime_env: Path,
) -> None:
    source_file = _write_text(tmp_path / "inputs" / "single.txt", "single-file processing")
    explicit_output = tmp_path / "custom" / "single-output.json"

    request = ProcessJobRequest(
        input_path=str(source_file.parent),
        source_files=[str(source_file)],
        output_path=str(explicit_output),
        output_format="json",
        include_evaluation=False,
    )

    result = JobService().run_process(request, work_dir=isolated_runtime_env)

    assert result.processed_count == 1
    assert Path(result.processed_files[0].output_path) == explicit_output
    assert explicit_output.exists()


def test_end_to_end_glob_request_processes_matching_files(
    tmp_path: Path,
    isolated_runtime_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs_dir = tmp_path / "inputs"
    _write_text(inputs_dir / "keep-a.txt", "alpha")
    _write_text(inputs_dir / "keep-b.txt", "beta")
    _write_text(inputs_dir / "ignore.md", "ignored by glob")

    monkeypatch.chdir(tmp_path)

    request = ProcessJobRequest(
        input_path="inputs/*.txt",
        output_path=str(tmp_path / "output"),
        output_format="json",
        include_evaluation=False,
    )

    result = JobService().run_process(request, work_dir=isolated_runtime_env)

    assert result.total_files == 2
    assert result.processed_count == 2
    assert result.failed_count == 0

    written_outputs = sorted((tmp_path / "output").rglob("*.json"))
    assert len(written_outputs) == 2
    assert {path.parent.name for path in written_outputs} == {"inputs"}


def test_end_to_end_semantic_requires_json_output(
    tmp_path: Path,
    isolated_runtime_env: Path,
) -> None:
    source_file = _write_text(tmp_path / "semantic.txt", "semantic stage compatibility")

    request = ProcessJobRequest(
        input_path=str(source_file),
        output_path=str(tmp_path / "output"),
        output_format="txt",
        include_semantic=True,
        include_evaluation=False,
    )

    result = JobService().run_process(request, work_dir=isolated_runtime_env)

    assert result.processed_count == 1
    assert result.semantic is not None
    assert result.semantic.status == "skipped"
    assert result.semantic.reason_code == "semantic_output_format_incompatible"
