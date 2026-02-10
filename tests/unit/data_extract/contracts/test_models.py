from __future__ import annotations

from data_extract.contracts import JobStatus, ProcessJobRequest, ProcessJobResult


def test_process_job_request_defaults() -> None:
    request = ProcessJobRequest(input_path="/tmp/input")

    assert request.output_format == "json"
    assert request.chunk_size == 512
    assert request.recursive is False
    assert request.source_files == []


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
