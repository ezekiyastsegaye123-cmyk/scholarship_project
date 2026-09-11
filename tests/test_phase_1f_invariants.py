"""Phase 1F: Epistemic Invariants Testing.

Explicitly asserts the fundamental truth tables and invariants:
- UNKNOWN != NO
- UNKNOWN != YES
- UNKNOWN != NOT_APPLICABLE
- UNKNOWN != INELIGIBLE

- CONFLICTING != NO
- CONFLICTING != YES
- CONFLICTING != VERIFIED

Proves that neither the eligibility evaluator nor the counselor silently
collapses epistemic uncertainty into unsupported definitive conclusions.
"""
from datetime import date
from unittest.mock import MagicMock
import pytest

from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    AlignmentLevel,
    FundingClassification,
    ReadinessLevel,
    RuleComparisonOp,
    RuleKind,
    RuleLogicalOp,
    TriState,
    VerificationState,
)
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.evaluator.logic import (
    evaluate_and_all,
    evaluate_not,
    evaluate_or_all,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


@pytest.fixture
def evaluator():
    return EligibilityEvaluator()


@pytest.fixture
def counselor():
    return ScholarshipCounselorService()


# ==============================================================================
# 1. LOGIC OPERATOR INVARIANTS (3-VALUED & 4-VALUED KLEENE LOGIC)
# ==============================================================================

def test_invariant_unknown_is_distinct_from_boolean_values():
    """UNKNOWN is distinct from YES, NO, NOT_APPLICABLE, and CONFLICTING."""
    assert TriState.UNKNOWN != TriState.YES
    assert TriState.UNKNOWN != TriState.NO
    assert TriState.UNKNOWN != TriState.NOT_APPLICABLE
    assert TriState.UNKNOWN != TriState.CONFLICTING


def test_invariant_conflicting_is_distinct_from_all_states():
    """CONFLICTING is distinct from YES, NO, UNKNOWN, and NOT_APPLICABLE."""
    assert TriState.CONFLICTING != TriState.YES
    assert TriState.CONFLICTING != TriState.NO
    assert TriState.CONFLICTING != TriState.UNKNOWN
    assert TriState.CONFLICTING != TriState.NOT_APPLICABLE


def test_invariant_logical_and_preserves_uncertainty():
    """AND logic preserves UNKNOWN and CONFLICTING unless definitively falsified by NO."""
    # Definite rejection (NO dominates AND)
    assert evaluate_and_all([TriState.UNKNOWN, TriState.NO]) == TriState.NO
    assert evaluate_and_all([TriState.CONFLICTING, TriState.NO]) == TriState.NO

    # Uncertainty cannot be confirmed to YES
    assert evaluate_and_all([TriState.UNKNOWN, TriState.YES]) == TriState.UNKNOWN
    assert evaluate_and_all([TriState.CONFLICTING, TriState.YES]) == TriState.CONFLICTING

    # Negation of uncertainty remains uncertain
    assert evaluate_not(TriState.UNKNOWN) == TriState.UNKNOWN
    assert evaluate_not(TriState.CONFLICTING) == TriState.CONFLICTING


def test_invariant_logical_or_preserves_uncertainty():
    """OR logic preserves UNKNOWN and CONFLICTING unless definitively satisfied by YES."""
    # Definite satisfaction (YES dominates OR)
    assert evaluate_or_all([TriState.UNKNOWN, TriState.YES]) == TriState.YES
    assert evaluate_or_all([TriState.CONFLICTING, TriState.YES]) == TriState.YES

    # Failing alternative leaves uncertainty unconfirmed
    assert evaluate_or_all([TriState.UNKNOWN, TriState.NO]) == TriState.UNKNOWN
    assert evaluate_or_all([TriState.CONFLICTING, TriState.NO]) == TriState.CONFLICTING


# ==============================================================================
# 2. EVALUATOR STATUS INVARIANTS
# ==============================================================================

def test_invariant_unknown_rule_does_not_produce_ineligible(evaluator):
    """An opportunity with missing student data produces NEEDS_INFORMATION, never INELIGIBLE or ELIGIBLE."""
    student = {"id": "s1"}  # Missing GPA
    rules = [
        MagicMock(
            rule_id="r_gpa",
            kind=RuleKind.REQUIRED.value,
            expression_json={"op": "GTE", "field": "gpa", "value": 3.5},
            description="Minimum 3.5 GPA",
            verification_status=VerificationState.VERIFIED.value,
            academic_cycle="2026-2027",
            source_evidence_snippet="Minimum GPA 3.5",
        )
    ]
    res = evaluator.evaluate_rules(
        rules=rules,
        student_profile=student,
        target_academic_cycle="2026-2027",
        opportunity_academic_cycle="2026-2027",
        verification_status=VerificationState.VERIFIED,
    )
    assert res.status == EligibilityStatus.NEEDS_INFORMATION
    assert res.status != EligibilityStatus.INELIGIBLE
    assert res.status != EligibilityStatus.ELIGIBLE
    assert len(res.unknown_rules) == 1
    assert len(res.failed_rules) == 0


def test_invariant_conflicting_fact_does_not_produce_eligible(evaluator):
    """Conflicting student facts produce NEEDS_REVIEW or NEEDS_INFORMATION, never silent ELIGIBLE."""
    # Conflicting GPA representation: list of contradictory values
    student = {"id": "s1", "gpa": [3.2, 3.9]}
    rules = [
        MagicMock(
            rule_id="r_gpa",
            kind=RuleKind.REQUIRED.value,
            expression_json={"op": "GTE", "field": "gpa", "value": 3.5},
            description="Minimum 3.5 GPA",
            verification_status=VerificationState.VERIFIED.value,
            academic_cycle="2026-2027",
            source_evidence_snippet="Minimum GPA 3.5",
        )
    ]
    res = evaluator.evaluate_rules(
        rules=rules,
        student_profile=student,
        target_academic_cycle="2026-2027",
        opportunity_academic_cycle="2026-2027",
        verification_status=VerificationState.VERIFIED,
    )
    assert res.status != EligibilityStatus.ELIGIBLE
    assert len(res.conflicting_rules) >= 1 or len(res.unknown_rules) >= 1


# ==============================================================================
# 3. COUNSELOR DIMENSIONAL INVARIANTS
# ==============================================================================

def test_invariant_counselor_testing_unknown_never_not_applicable(counselor):
    """When testing policy is UNKNOWN, readiness is UNKNOWN, never NOT_APPLICABLE."""
    profile = {"sat_score": 1400}
    opp = MagicMock(
        id="opp-test-inv",
        title="Testing Invariant Opp",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.UNKNOWN.value,
        requires_act=TriState.UNKNOWN.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.testing_readiness.level == ReadinessLevel.UNKNOWN
    assert res.testing_readiness.level != ReadinessLevel.NOT_APPLICABLE


def test_invariant_counselor_preparation_unknown_never_needs_preparation(counselor):
    """When requirements exist but student recorded no preparation, level is UNKNOWN, not NEEDS_PREPARATION."""
    profile = {}  # No prepared_materials field at all
    opp = MagicMock(
        id="opp-prep-inv",
        title="Prep Invariant Opp",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[],
        application_requirements=[
            MagicMock(title="Essay", kind=RuleKind.REQUIRED.value, source_evidence_snippet="Essay required")
        ],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.application_readiness.level == ReadinessLevel.UNKNOWN
    assert res.application_readiness.level != ReadinessLevel.NEEDS_PREPARATION


def test_invariant_counselor_unsubstantiated_funding_never_full_funding(counselor):
    """Tuition-only funding is strictly FULL_TUITION and never promoted to FULL_FUNDING."""
    profile = {}
    opp = MagicMock(
        id="opp-fund-inv",
        title="Tuition Only Opp",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=MagicMock(
            funding_classification=FundingClassification.FULL_TUITION.value,
            funding_components=[],
            is_renewable=TriState.YES.value,
            estimated_annual_value_usd=40000.0,
        ),
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.funding_assessment.funding_classification == FundingClassification.FULL_TUITION
    assert res.funding_assessment.funding_classification != FundingClassification.FULL_FUNDING
