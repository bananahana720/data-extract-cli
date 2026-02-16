"""Integration tests for JobService/session infrastructure behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.contracts import JobStatus, ProcessJobRequest
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


def test_job_service_run_process_persists_session_state(
    tmp_path: Path,
    isolated_runtime_env: Path,
) -> None:
    source_dir = tmp_path / "source"
    _write_text(source_dir / "first.txt", "first file")
    _write_text(source_dir / "second.txt", "second file")
    output_dir = tmp_path / "output"

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        include_evaluation=False,
    )

    result = JobService().run_process(request, work_dir=isolated_runtime_env)

    assert result.status == JobStatus.COMPLETED
    assert result.processed_count == 2
    assert result.failed_count == 0
    assert result.session_id is not None

    # Successful sessions are cleaned up after completion.
    session_dir = isolated_runtime_env / ".data-extract-session"
    if session_dir.exists():
        active_sessions = list(session_dir.glob("session-*.json"))
        assert active_sessions == []


def test_job_service_excludes_existing_output_tree_from_discovery(
    tmp_path: Path,
    isolated_runtime_env: Path,
) -> None:
    source_dir = tmp_path / "source"
    output_dir = source_dir / "output"
    _write_text(source_dir / "input.txt", "source text")
    _write_text(output_dir / "already.txt", "generated output should be excluded")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        recursive=True,
        include_evaluation=False,
    )

    result = JobService().run_process(request, work_dir=isolated_runtime_env)

    assert result.total_files == 1
    assert result.processed_count == 1
    assert Path(result.processed_files[0].path).name == "input.txt"
    assert (output_dir / "input.json").exists()
