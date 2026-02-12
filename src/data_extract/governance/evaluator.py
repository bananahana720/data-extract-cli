"""Deterministic governance evaluator for process outcomes."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import yaml

from data_extract.contracts import (
    EvaluationVerdict,
    GovernanceCheckResult,
    GovernanceEvaluationOutcome,
    GovernanceEvidenceRef,
    GovernanceMilestoneResult,
    ProcessJobResult,
    SemanticOutcome,
)

from .models import GovernanceEvaluationPolicy, GovernancePolicyCheck


def _policy_filename(policy_id: str) -> str:
    return f"eval_policy_{policy_id}.yaml"


def _repo_policy_search_paths() -> tuple[Path, ...]:
    module_repo_root = Path(__file__).resolve().parents[3]
    return (
        module_repo_root / "config" / "governance",
        Path.cwd() / "config" / "governance",
    )


def _dedupe_stable(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


class GovernanceEvaluator:
    """Evaluate a process result against a governance policy."""

    def load_policy(self, policy_id: str) -> GovernanceEvaluationPolicy:
        """Load a governance policy by id from package resources or local config."""
        filename = _policy_filename(policy_id)

        package_policy = (
            resources.files("data_extract.governance").joinpath("policies").joinpath(filename)
        )
        payload: Any = None
        searched_paths: list[str] = []

        if package_policy.is_file():
            payload = yaml.safe_load(package_policy.read_text(encoding="utf-8")) or {}
        else:
            for policy_dir in _repo_policy_search_paths():
                candidate = policy_dir / filename
                searched_paths.append(str(candidate))
                if not candidate.exists():
                    continue
                payload = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
                break

        if payload is None:
            raise FileNotFoundError(
                f"Evaluation policy not found: {policy_id} (searched: {', '.join(searched_paths)})"
            )
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid evaluation policy payload: {policy_id}")
        payload.setdefault("policy_id", policy_id)
        return GovernanceEvaluationPolicy.model_validate(payload)

    def evaluate(
        self,
        *,
        result: ProcessJobResult,
        stage_totals_ms: Dict[str, float],
        semantic_outcome: SemanticOutcome | None,
        policy_id: str,
    ) -> GovernanceEvaluationOutcome:
        """Evaluate result against configured governance policy."""
        policy = self.load_policy(policy_id)
        metrics = self._collect_metrics(
            result=result,
            stage_totals_ms=stage_totals_ms,
            semantic_outcome=semantic_outcome,
        )

        milestone_results: list[GovernanceMilestoneResult] = []
        failed_critical_checks: list[str] = []
        reason_codes: list[str] = []
        weighted_sum = 0.0
        weight_total = 0.0

        semantic_disabled = self._is_semantic_disabled(semantic_outcome)

        for milestone in policy.milestones:
            if milestone.skip_when_semantic_disabled and semantic_disabled:
                milestone_results.append(
                    GovernanceMilestoneResult(
                        milestone_id=milestone.milestone_id,
                        title=milestone.title,
                        weight=milestone.weight,
                        status="skipped",
                        score=None,
                        skipped=True,
                        critical_failed=False,
                        checks=[],
                        reason_codes=[],
                    )
                )
                continue

            check_results: list[GovernanceCheckResult] = []
            milestone_reason_codes: list[str] = []
            critical_failed = False
            check_weight_sum = 0.0
            check_weighted_scores = 0.0

            for check in milestone.checks:
                evaluated = self._evaluate_check(check=check, metrics=metrics)
                check_results.append(evaluated)
                check_weight_sum += check.weight
                check_weighted_scores += evaluated.score * check.weight

                if not evaluated.passed:
                    milestone_reason_codes.append(check.reason_code)
                    if check.critical:
                        critical_failed = True
                        failed_critical_checks.append(check.check_id)

            milestone_score = (
                check_weighted_scores / check_weight_sum if check_weight_sum > 0 else 0.0
            )
            milestone_status = (
                "failed"
                if critical_failed or any(not check.passed for check in check_results)
                else "passed"
            )
            milestone_reason_codes = _dedupe_stable(milestone_reason_codes)
            reason_codes.extend(milestone_reason_codes)

            milestone_results.append(
                GovernanceMilestoneResult(
                    milestone_id=milestone.milestone_id,
                    title=milestone.title,
                    weight=milestone.weight,
                    status=milestone_status,
                    score=round(milestone_score, 4),
                    skipped=False,
                    critical_failed=critical_failed,
                    checks=check_results,
                    reason_codes=milestone_reason_codes,
                )
            )

            weighted_sum += milestone_score * milestone.weight
            weight_total += milestone.weight

        overall_score = round((weighted_sum / weight_total) if weight_total > 0 else 0.0, 4)
        reason_codes = _dedupe_stable(reason_codes)
        failed_critical_checks = _dedupe_stable(failed_critical_checks)
        verdict = self._resolve_verdict(
            overall_score=overall_score,
            has_critical_failure=bool(failed_critical_checks),
            good_min=policy.thresholds.good_min,
            watch_min=policy.thresholds.watch_min,
        )

        return GovernanceEvaluationOutcome(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            overall_score=overall_score,
            verdict=verdict,
            milestones=milestone_results,
            failed_critical_checks=failed_critical_checks,
            reason_codes=reason_codes,
            metadata={
                "semantic_status": semantic_outcome.status if semantic_outcome else "disabled",
                "thresholds": {
                    "good_min": policy.thresholds.good_min,
                    "watch_min": policy.thresholds.watch_min,
                },
            },
        )

    @staticmethod
    def _is_semantic_disabled(semantic_outcome: SemanticOutcome | None) -> bool:
        if semantic_outcome is None:
            return True
        return str(semantic_outcome.status).lower() == "disabled"

    @staticmethod
    def _resolve_verdict(
        *,
        overall_score: float,
        has_critical_failure: bool,
        good_min: float,
        watch_min: float,
    ) -> EvaluationVerdict:
        if has_critical_failure:
            return EvaluationVerdict.BAD
        if overall_score >= good_min:
            return EvaluationVerdict.GOOD
        if overall_score >= watch_min:
            return EvaluationVerdict.WATCH
        return EvaluationVerdict.BAD

    def _evaluate_check(
        self,
        *,
        check: GovernancePolicyCheck,
        metrics: Dict[str, Any],
    ) -> GovernanceCheckResult:
        observed = metrics.get(check.metric)
        passed, score = self._score_check(
            observed=observed,
            operator=check.operator,
            target=check.target,
        )
        return GovernanceCheckResult(
            check_id=check.check_id,
            metric=check.metric,
            critical=check.critical,
            weight=check.weight,
            operator=check.operator,
            target=check.target,
            observed=observed,
            passed=passed,
            score=score,
            reason_code=check.reason_code if not passed else None,
            evidence=[
                GovernanceEvidenceRef(
                    field_path=f"metrics.{check.metric}",
                    value_snapshot=observed,
                )
            ],
        )

    @staticmethod
    def _score_check(*, observed: Any, operator: str, target: Any) -> Tuple[bool, float]:
        if observed is None:
            return False, 0.0

        normalized_operator = str(operator).strip().lower()
        if normalized_operator == "bool_true":
            passed = bool(observed) is True
            return passed, 100.0 if passed else 0.0

        if normalized_operator == "equals":
            passed = observed == target
            return passed, 100.0 if passed else 0.0

        if normalized_operator == "in":
            options = set(target or [])
            passed = observed in options
            return passed, 100.0 if passed else 0.0

        if normalized_operator == "gte":
            try:
                observed_f = float(observed)
                target_f = float(target)
            except (TypeError, ValueError):
                return False, 0.0
            passed = observed_f >= target_f
            if target_f <= 0:
                return passed, 100.0 if passed else 0.0
            score = min(100.0, max(0.0, (observed_f / target_f) * 100.0))
            return passed, round(score, 4)

        if normalized_operator == "lte":
            try:
                observed_f = float(observed)
                target_f = float(target)
            except (TypeError, ValueError):
                return False, 0.0
            passed = observed_f <= target_f
            if passed:
                return True, 100.0
            denominator = max(abs(target_f), 1.0)
            penalty_ratio = (observed_f - target_f) / denominator
            score = max(0.0, 100.0 - (penalty_ratio * 100.0))
            return False, round(score, 4)

        return False, 0.0

    @staticmethod
    def _collect_metrics(
        *,
        result: ProcessJobResult,
        stage_totals_ms: Dict[str, float],
        semantic_outcome: SemanticOutcome | None,
    ) -> Dict[str, Any]:
        total_files = int(result.total_files)
        processed_count = int(result.processed_count)
        failed_count = int(result.failed_count)
        skipped_count = int(result.skipped_count)

        denominator = total_files if total_files > 0 else 1
        processed_denominator = processed_count if processed_count > 0 else 1

        normalize_coverage = (
            sum(
                1
                for item in result.processed_files
                if float(item.stage_timings_ms.get("normalize", 0.0)) > 0.0
            )
            / processed_denominator
        )
        chunk_nonzero_ratio = (
            sum(1 for item in result.processed_files if int(item.chunk_count) > 0)
            / processed_denominator
        )
        output_exists_ratio = (
            sum(1 for item in result.processed_files if Path(item.output_path).exists())
            / processed_denominator
        )

        semantic_status = semantic_outcome.status if semantic_outcome else "disabled"
        semantic_required_status_ok = semantic_status == "completed"
        semantic_summary_present = bool(semantic_outcome and semantic_outcome.summary)

        accounted = processed_count + failed_count + skipped_count
        metrics: Dict[str, Any] = {
            "extract.counts_reconciled": accounted == total_files,
            "extract.processed_ratio": processed_count / denominator,
            "normalize.stage_timing_coverage": normalize_coverage,
            "normalize.failure_ratio": failed_count / denominator,
            "chunk.nonzero_chunk_ratio": chunk_nonzero_ratio,
            "chunk.stage_present": float(stage_totals_ms.get("chunk", 0.0)) > 0.0,
            "semantic.required_status_ok": semantic_required_status_ok,
            "semantic.summary_present": semantic_summary_present,
            "output.output_exists_ratio": output_exists_ratio,
            "output.stage_present": float(stage_totals_ms.get("output", 0.0)) > 0.0,
            "output.output_dir_exists": bool(
                result.output_dir and Path(result.output_dir).exists()
            ),
        }
        return metrics
