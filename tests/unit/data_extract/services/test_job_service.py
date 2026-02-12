from __future__ import annotations

from pathlib import Path

from data_extract.contracts import JobStatus, ProcessJobRequest
from data_extract.services import JobService, StatusService


def test_run_process_generates_real_output_for_txt(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    sample_file = source_dir / "sample.txt"
    sample_file.write_text("alpha beta gamma", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=16,
    )

    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 1
    assert result.failed_count == 0
    assert (output_dir / "sample.json").exists()
    assert result.request_hash is not None
    assert result.evaluation is not None


def test_run_process_avoids_output_collisions_for_duplicate_stems(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-dupes"
    output_dir = tmp_path / "output-dupes"
    (source_dir / "a").mkdir(parents=True)
    (source_dir / "b").mkdir(parents=True)
    (source_dir / "a" / "same.txt").write_text("alpha", encoding="utf-8")
    (source_dir / "b" / "same.txt").write_text("beta", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=16,
        recursive=True,
    )
    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 2
    assert (output_dir / "a" / "same.json").exists()
    assert (output_dir / "b" / "same.json").exists()
    assert all(outcome.source_key for outcome in result.processed_files)


def test_run_process_can_emit_semantic_artifacts(tmp_path: Path) -> None:
    source_dir = tmp_path / "semantic-source"
    output_dir = tmp_path / "semantic-output"
    source_dir.mkdir()
    (source_dir / "a.txt").write_text("alpha beta gamma delta epsilon", encoding="utf-8")
    (source_dir / "b.txt").write_text("alpha beta gamma zeta eta theta", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=64,
        include_semantic=True,
        semantic_report=True,
        semantic_export_graph=True,
    )

    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 2
    assert result.semantic is not None
    assert result.semantic.status in {"completed", "failed", "skipped"}
    if result.semantic.status == "completed":
        artifact_types = {artifact.artifact_type for artifact in result.semantic.artifacts}
        assert "summary" in artifact_types
        assert "graph" in artifact_types


def test_run_process_incremental_persists_state_for_status(tmp_path: Path) -> None:
    source_dir = tmp_path / "incremental-source"
    output_dir = source_dir / "output"
    source_dir.mkdir(parents=True)
    sample_file = source_dir / "sample.txt"
    sample_file.write_text("incremental payload", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=64,
        incremental=True,
    )
    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 1
    status = StatusService().get_status(source_dir=source_dir, output_dir=output_dir)
    assert status["state_file_present"] is True
    assert status["total_files"] == 1
    assert str(sample_file.resolve()) in status["tracked_files"]


def test_run_process_semantic_incompatible_output_sets_reason_code(tmp_path: Path) -> None:
    source_dir = tmp_path / "semantic-incompatible-source"
    output_dir = tmp_path / "semantic-incompatible-output"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.txt").write_text("alpha beta gamma", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="txt",
        chunk_size=64,
        include_semantic=True,
    )

    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 1
    assert result.semantic is not None
    assert result.semantic.status == "skipped"
    assert result.semantic.reason_code == "semantic_output_format_incompatible"


def test_run_process_fail_on_bad_evaluation_sets_nonzero_exit_code(tmp_path: Path) -> None:
    source_dir = tmp_path / "eval-fail-source"
    output_dir = tmp_path / "eval-fail-output"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.txt").write_text("alpha beta gamma", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="txt",
        chunk_size=64,
        include_semantic=True,
        include_evaluation=True,
        evaluation_fail_on_bad=True,
    )

    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 1
    assert result.failed_count == 0
    assert result.evaluation is not None
    assert result.evaluation.verdict == "bad"
    assert result.exit_code == 1
    assert result.status == JobStatus.FAILED


def test_run_process_excludes_existing_outputs_from_source_discovery(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-with-output"
    output_dir = source_dir / "output"
    output_dir.mkdir(parents=True)
    source_file = source_dir / "source.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("real source", encoding="utf-8")
    generated_output = output_dir / "generated.txt"
    generated_output.write_text("already generated artifact", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=64,
        recursive=True,
    )
    result = JobService().run_process(request, work_dir=tmp_path)

    processed_sources = {Path(item.path).resolve() for item in result.processed_files}
    assert result.processed_count == 1
    assert source_file.resolve() in processed_sources
    assert generated_output.resolve() not in processed_sources


def test_request_hash_ignores_outputs_inside_source_tree(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-hash"
    output_dir = source_dir / "output"
    source_dir.mkdir(parents=True)
    (source_dir / "source.txt").write_text("hash baseline", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="txt",
        chunk_size=32,
        recursive=True,
    )

    service = JobService()
    first = service.run_process(request, work_dir=tmp_path)
    second = service.run_process(request, work_dir=tmp_path)

    assert first.request_hash is not None
    assert second.request_hash == first.request_hash
