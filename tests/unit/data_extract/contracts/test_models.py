from __future__ import annotations

from data_extract.contracts import (
    JobStatus,
    ProcessedFileOutcome,
    ProcessJobRequest,
    ProcessJobResult,
    SemanticOutcome,
)


def test_process_job_request_defaults() -> None:
    request = ProcessJobRequest(input_path="/tmp/input")

    assert request.output_format == "json"
    assert request.chunk_size == 512
    assert request.recursive is False
    assert request.source_files == []
    assert request.idempotency_key is None
    assert request.semantic_report is None
    assert request.semantic_export_graph is None


def test_process_job_result_status_enum() -> None:
    result = ProcessJobResult(
        job_id="job-1",
        status=JobStatus.COMPLETED,
        total_files=1,
        processed_count=1,
        failed_count=0,
        output_dir="/tmp/out",
    )

    assert result.status == JobStatus.COMPLETED
    assert result.exit_code == 0
    assert result.artifact_dir is None
    assert result.request_hash is None
    assert result.semantic is None


def test_processed_file_outcome_supports_source_key() -> None:
    outcome = ProcessedFileOutcome(path="/tmp/a.txt", output_path="/tmp/out/a.json", source_key="abc123")
    assert outcome.source_key == "abc123"


def test_semantic_outcome_defaults() -> None:
    outcome = SemanticOutcome()
    assert outcome.status == "disabled"
    assert outcome.artifacts == []
