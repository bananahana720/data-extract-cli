from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.contracts import (
    EvaluationVerdict,
    JobStatus,
    ProcessedFileOutcome,
    ProcessJobResult,
    SemanticOutcome,
)
from data_extract.governance.evaluator import GovernanceEvaluator
from data_extract.governance.models import (
    GovernanceEvaluationPolicy,
    GovernancePolicyCheck,
    GovernancePolicyMilestone,
    GovernancePolicyThresholds,
)


def _base_result(tmp_path: Path) -> ProcessJobResult:
    output_file = tmp_path / "sample.json"
    output_file.write_text("{}", encoding="utf-8")
    return ProcessJobResult(
        job_id="job-1",
        status=JobStatus.COMPLETED,
        total_files=1,
        processed_count=1,
        failed_count=0,
        output_dir=str(tmp_path),
        processed_files=[
            ProcessedFileOutcome(
                path=str(tmp_path / "sample.txt"),
                output_path=str(output_file),
                chunk_count=1,
                stage_timings_ms={"normalize": 1.2},
            )
        ],
    )


def test_critical_failure_forces_bad_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    policy = GovernanceEvaluationPolicy(
        policy_id="custom",
        version="1.0",
        thresholds=GovernancePolicyThresholds(good_min=85, watch_min=70),
        milestones=[
            GovernancePolicyMilestone(
                milestone_id="m1",
                title="M1",
                weight=1,
                checks=[
                    GovernancePolicyCheck(
                        check_id="critical_check",
                        metric="critical.metric",
                        operator="equals",
                        target=True,
                        critical=True,
                        reason_code="CRITICAL_FAIL",
                    ),
                    GovernancePolicyCheck(
                        check_id="score_check",
                        metric="score.metric",
                        operator="gte",
                        target=1.0,
                        critical=False,
                        reason_code="LOW_SCORE",
                    ),
                ],
            )
        ],
    )

    monkeypatch.setattr(GovernanceEvaluator, "load_policy", lambda _self, _id: policy)
    monkeypatch.setattr(
        GovernanceEvaluator,
        "_collect_metrics",
        staticmethod(lambda **_: {"critical.metric": False, "score.metric": 2.0}),
    )

    outcome = GovernanceEvaluator().evaluate(
        result=_base_result(tmp_path),
        stage_totals_ms={"chunk": 1.0, "output": 1.0},
        semantic_outcome=SemanticOutcome(status="disabled"),
        policy_id="custom",
    )

    assert outcome.verdict == EvaluationVerdict.BAD
    assert outcome.failed_critical_checks == ["critical_check"]
    assert outcome.reason_codes == ["CRITICAL_FAIL"]


def test_verdict_boundaries_at_85_and_70(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy = GovernanceEvaluationPolicy(
        policy_id="custom",
        version="1.0",
        thresholds=GovernancePolicyThresholds(good_min=85, watch_min=70),
        milestones=[
            GovernancePolicyMilestone(
                milestone_id="m1",
                title="M1",
                weight=1,
                checks=[
                    GovernancePolicyCheck(
                        check_id="check_1",
                        metric="m1.metric",
                        operator="gte",
                        target=1.0,
                        reason_code="M1_FAIL",
                    )
                ],
            ),
            GovernancePolicyMilestone(
                milestone_id="m2",
                title="M2",
                weight=1,
                checks=[
                    GovernancePolicyCheck(
                        check_id="check_2",
                        metric="m2.metric",
                        operator="gte",
                        target=1.0,
                        reason_code="M2_FAIL",
                    )
                ],
            ),
        ],
    )
    monkeypatch.setattr(GovernanceEvaluator, "load_policy", lambda _self, _id: policy)

    evaluator = GovernanceEvaluator()
    monkeypatch.setattr(
        GovernanceEvaluator,
        "_collect_metrics",
        staticmethod(lambda **_: {"m1.metric": 1.0, "m2.metric": 0.7}),
    )
    outcome_good = evaluator.evaluate(
        result=_base_result(tmp_path),
        stage_totals_ms={},
        semantic_outcome=SemanticOutcome(status="disabled"),
        policy_id="custom",
    )
    assert outcome_good.overall_score == 85.0
    assert outcome_good.verdict == EvaluationVerdict.GOOD

    monkeypatch.setattr(
        GovernanceEvaluator,
        "_collect_metrics",
        staticmethod(lambda **_: {"m1.metric": 1.0, "m2.metric": 0.4}),
    )
    outcome_watch = evaluator.evaluate(
        result=_base_result(tmp_path),
        stage_totals_ms={},
        semantic_outcome=SemanticOutcome(status="disabled"),
        policy_id="custom",
    )
    assert outcome_watch.overall_score == 70.0
    assert outcome_watch.verdict == EvaluationVerdict.WATCH


def test_semantic_disabled_skips_semantic_milestone(tmp_path: Path) -> None:
    outcome = GovernanceEvaluator().evaluate(
        result=_base_result(tmp_path),
        stage_totals_ms={"chunk": 1.0, "output": 1.0},
        semantic_outcome=SemanticOutcome(status="disabled"),
        policy_id="baseline_v1",
    )

    semantic_milestone = next(m for m in outcome.milestones if m.milestone_id == "semantic")
    assert semantic_milestone.skipped is True
    assert semantic_milestone.score is None
    assert outcome.overall_score == 100.0


def test_load_policy_prefers_package_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "data_extract.governance.evaluator._repo_policy_search_paths",
        lambda: (Path("/tmp/nonexistent-policy-dir"),),
    )

    policy = GovernanceEvaluator().load_policy("baseline_v1")

    assert policy.policy_id == "baseline_v1"
    assert policy.milestones


def test_reason_codes_have_deterministic_stable_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    policy = GovernanceEvaluationPolicy(
        policy_id="order",
        version="1.0",
        thresholds=GovernancePolicyThresholds(good_min=85, watch_min=70),
        milestones=[
            GovernancePolicyMilestone(
                milestone_id="m1",
                title="M1",
                weight=1,
                checks=[
                    GovernancePolicyCheck(
                        check_id="c1",
                        metric="m1.c1",
                        operator="bool_true",
                        reason_code="R2",
                    ),
                    GovernancePolicyCheck(
                        check_id="c2",
                        metric="m1.c2",
                        operator="bool_true",
                        reason_code="R1",
                    ),
                ],
            ),
            GovernancePolicyMilestone(
                milestone_id="m2",
                title="M2",
                weight=1,
                checks=[
                    GovernancePolicyCheck(
                        check_id="c3",
                        metric="m2.c3",
                        operator="bool_true",
                        reason_code="R2",
                    )
                ],
            ),
        ],
    )
    monkeypatch.setattr(GovernanceEvaluator, "load_policy", lambda _self, _id: policy)
    monkeypatch.setattr(
        GovernanceEvaluator,
        "_collect_metrics",
        staticmethod(lambda **_: {"m1.c1": False, "m1.c2": False, "m2.c3": False}),
    )

    outcome = GovernanceEvaluator().evaluate(
        result=_base_result(tmp_path),
        stage_totals_ms={},
        semantic_outcome=SemanticOutcome(status="disabled"),
        policy_id="order",
    )

    assert outcome.reason_codes == ["R2", "R1"]
