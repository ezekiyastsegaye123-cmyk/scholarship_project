"""Pydantic schemas for deterministic eligibility evaluation results.

Phase 1D Guarantees:
- Strict preservation of TriState semantics (YES, NO, UNKNOWN, NOT_APPLICABLE, CONFLICTING).
- No numerical scores (no fit_score, match_score, competitiveness_score, trust_score).
- No probabilistic rankings or acceptance percentages.
- Fully auditable with explicit explanations and provenance references.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import RuleKind, TriState, VerificationState


class EligibilityStatus(str, Enum):
    """Aggregate eligibility decision status."""
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    GATED_UNVERIFIED = "GATED_UNVERIFIED"
    OUTDATED_CYCLE = "OUTDATED_CYCLE"


class RuleEvaluationResult(BaseModel):
    """Result of evaluating a single rule or sub-expression."""
    rule_id: str = Field(..., description="Unique identifier of the rule or expression node")
    kind: RuleKind = Field(RuleKind.REQUIRED, description="Constraint enforcement kind")
    status: TriState = Field(..., description="Tri-state evaluation outcome")
    explanation: str = Field(..., description="Deterministic human-readable explanation")
    field: Optional[str] = Field(None, description="Field evaluated if comparison")
    expected_value: Optional[Any] = Field(None, description="Expected value from rule")
    actual_value: Optional[Any] = Field(None, description="Actual student profile value")
    scale: Optional[float] = Field(None, description="Expected scale (e.g. GPA scale)")
    student_scale: Optional[float] = Field(None, description="Student's scale if applicable")
    evidence_snippet: Optional[str] = Field(None, description="Source provenance evidence text")
    is_verified: bool = Field(True, description="True if rule is verified; False if unverified or partially verified")
    sub_results: List["RuleEvaluationResult"] = Field(default_factory=list, description="Operands evaluation for composite expressions")

    model_config = ConfigDict(from_attributes=True)


class EligibilityEvaluationResult(BaseModel):
    """Complete aggregated evaluation outcome for an opportunity and student."""
    opportunity_id: Optional[str] = Field(None, description="Opportunity UUID")
    opportunity_title: Optional[str] = Field(None, description="Opportunity title")
    status: EligibilityStatus = Field(..., description="Overall aggregate status")
    target_academic_cycle: str = Field(..., description="Target academic cycle evaluated against")
    opportunity_academic_cycle: Optional[str] = Field(None, description="Cycle for which opportunity was verified")
    verification_status: Optional[VerificationState] = Field(None, description="Verification status of the opportunity")
    is_gated: bool = Field(False, description="True if evaluation was halted by verification or cycle gating")
    evaluation_contains_unverified_facts: bool = Field(
        False,
        description="True if evaluation contains partially verified or unverified facts/rules",
    )
    satisfied_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Required rules that evaluated to YES")
    failed_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Required rules that evaluated to NO")
    unknown_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Required rules that evaluated to UNKNOWN")
    conflicting_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Required rules that evaluated to CONFLICTING")
    not_applicable_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Rules that evaluated to NOT_APPLICABLE")
    supplementary_rules: List[RuleEvaluationResult] = Field(default_factory=list, description="Non-required rules (CONDITIONAL, PREFERRED)")
    explanations: List[str] = Field(default_factory=list, description="Ordered human-readable explanations")
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, description="Audit trail metadata")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Evaluation timestamp")

    model_config = ConfigDict(from_attributes=True)
