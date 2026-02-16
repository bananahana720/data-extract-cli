"""Integration tests for PipelineService orchestration paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.services.pipeline_service import PipelineService

pytestmark = [pytest.mark.P0, pytest.mark.integration]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_process_files_collects_failures_when_continue_on_error(tmp_path: Path) -> None:
    good_a = _write_text(tmp_path / "good-a.txt", "alpha beta gamma")
    bad_file = _write_text(tmp_path / "bad.xyz", "unsupported")
    good_b = _write_text(tmp_path / "good-b.txt", "delta epsilon zeta")

    run = PipelineService().process_files(
        files=[good_a, bad_file, good_b],
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=4,
        continue_on_error=True,
        include_semantic=False,
        pipeline_profile="legacy",
        source_root=tmp_path,
    )

    assert {item.source_path.name for item in run.processed} == {"good-a.txt", "good-b.txt"}
    assert len(run.failed) == 1
    assert run.failed[0].source_path.name == "bad.xyz"
    assert run.failed[0].error_type == "ValueError"
    assert {"extract", "normalize", "chunk", "semantic", "output"}.issubset(run.stage_totals_ms)


def test_process_files_stops_after_first_failure_when_continue_disabled(tmp_path: Path) -> None:
    bad_file = _write_text(tmp_path / "first.xyz", "unsupported")
    good_file = _write_text(tmp_path / "second.txt", "should not process")

    run = PipelineService().process_files(
        files=[bad_file, good_file],
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=4,
        continue_on_error=False,
        include_semantic=False,
        pipeline_profile="legacy",
        source_root=tmp_path,
    )

    assert len(run.failed) == 1
    assert run.failed[0].source_path.name == "first.xyz"
    assert run.processed == []
    assert not (tmp_path / "output" / "second.json").exists()


def test_process_files_parallel_workers_handle_multiple_inputs(tmp_path: Path) -> None:
    files = [
        _write_text(tmp_path / "one.txt", "one two three"),
        _write_text(tmp_path / "two.txt", "four five six"),
        _write_text(tmp_path / "three.txt", "seven eight nine"),
    ]

    run = PipelineService().process_files(
        files=files,
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=2,
        workers=3,
        continue_on_error=True,
        include_semantic=False,
        pipeline_profile="legacy",
        source_root=tmp_path,
    )

    assert len(run.processed) == 3
    assert run.failed == []
    assert {item.source_path.name for item in run.processed} == {"one.txt", "two.txt", "three.txt"}
