from __future__ import annotations

from data_extract.contracts import (
    EvaluationVerdict,
    GovernanceCheckResult,
    GovernanceEvaluationOutcome,
    GovernanceMilestoneResult,
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
    assert request.include_evaluation is True
    assert request.evaluation_policy == "baseline_v1"
    assert request.evaluation_fail_on_bad is False


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
    assert result.evaluation is None


def test_processed_file_outcome_supports_source_key() -> None:
    outcome = ProcessedFileOutcome(
        path="/tmp/a.txt", output_path="/tmp/out/a.json", source_key="abc123"
    )
    assert outcome.source_key == "abc123"


def test_semantic_outcome_defaults() -> None:
    outcome = SemanticOutcome()
    assert outcome.status == "disabled"
    assert outcome.reason_code is None
    assert outcome.artifacts == []


def test_process_job_result_semantic_skip_reason_code_contract() -> None:
    result = ProcessJobResult(
        job_id="job-2",
        status=JobStatus.COMPLETED,
        total_files=1,
        processed_count=1,
        failed_count=0,
        output_dir="/tmp/out",
        semantic=SemanticOutcome(
            status="skipped",
            reason_code="semantic_output_format_incompatible",
            message="Semantic stage requires JSON output format for chunk loading.",
        ),
    )

    payload = result.model_dump()
    assert payload["semantic"]["status"] == "skipped"
    assert payload["semantic"]["reason_code"] == "semantic_output_format_incompatible"


def test_governance_outcome_contract_shape() -> None:
    outcome = GovernanceEvaluationOutcome(
        policy_id="baseline_v1",
        policy_version="1.0",
        overall_score=91.2,
        verdict=EvaluationVerdict.GOOD,
        milestones=[
            GovernanceMilestoneResult(
                milestone_id="extract",
                title="Extract Integrity",
                score=100.0,
                checks=[
                    GovernanceCheckResult(
                        check_id="extract_count_reconciled",
                        metric="extract.counts_reconciled",
                        passed=True,
                        score=100.0,
                    )
                ],
            )
        ],
    )

    payload = outcome.model_dump()
    assert payload["policy_id"] == "baseline_v1"
    assert payload["verdict"] == "good"
    assert payload["milestones"][0]["checks"][0]["metric"] == "extract.counts_reconciled"
