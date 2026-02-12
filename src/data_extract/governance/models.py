"""Governance policy models for evaluation scoring."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

from data_extract.contracts import EvaluationVerdict


class GovernancePolicyThresholds(BaseModel):
    """Score thresholds that map to governance verdicts."""

    good_min: float = Field(default=85.0, ge=0.0, le=100.0)
    watch_min: float = Field(default=70.0, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "GovernancePolicyThresholds":
        if self.good_min < self.watch_min:
            raise ValueError("good_min must be greater than or equal to watch_min")
        return self


class GovernancePolicyCheck(BaseModel):
    """Single policy check attached to a milestone."""

    check_id: str
    metric: str
    operator: str = "gte"
    target: Optional[Any] = None
    critical: bool = False
    weight: float = Field(default=1.0, gt=0.0)
    reason_code: str
    description: str = ""


class GovernancePolicyMilestone(BaseModel):
    """Policy milestone with checks and scoring weight."""

    milestone_id: str
    title: str
    weight: float = Field(default=1.0, gt=0.0)
    skip_when_semantic_disabled: bool = False
    checks: List[GovernancePolicyCheck] = Field(default_factory=list)


class GovernanceEvaluationPolicy(BaseModel):
    """Policy definition loaded from YAML."""

    policy_id: str
    version: str = "1.0"
    thresholds: GovernancePolicyThresholds = Field(default_factory=GovernancePolicyThresholds)
    milestones: List[GovernancePolicyMilestone] = Field(default_factory=list)


class GovernanceEvaluationSummary(BaseModel):
    """Minimal summary of evaluation outcome."""

    overall_score: float = Field(ge=0.0, le=100.0)
    verdict: EvaluationVerdict
    failed_critical_checks: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
