"""Phase 1F: Adversarial and Property-Style Testing.

Validates resilience and safe degradation against:
- Empty and malformed student profiles
- Missing opportunity relations (award, deadlines, sources, requirements)
- Malformed rule ASTs, unknown operators, invalid operand counts, depth > 5
- Unauthorized field injections
- Duplicate deadlines, impossible dates, conflicting provider rules
- Safe degradation without fabricating eligibility or crashing.
"""
from datetime import date
from unittest.mock import MagicMock
import pytest

from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    AlignmentLevel,
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    ReadinessLevel,
    RequirementKind,
    RuleComparisonOp,
    RuleKind,
    RuleLogicalOp,
    TriState,
    VerificationState,
)
from scholarship_intelligence.domain.rules import MAX_RULE_DEPTH
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.evaluator.validator import (
    RuleValidationError,
    validate_rule_expression,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


@pytest.fixture
def counselor():
    return ScholarshipCounselorService()


@pytest.fixture
def evaluator():
    return EligibilityEvaluator()


# ==============================================================================
# 1. EMPTY AND MALFORMED STUDENT PROFILES
# ==============================================================================

def test_adversarial_completely_empty_student_profile(counselor):
    """An empty dict profile should degrade safely to UNKNOWN / NOT_ASSESSABLE without crashing."""
    profile = {}
    opp = MagicMock(
        id="opp-empty-prof",
        title="Test Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.UNKNOWN.value,
        requires_act=TriState.UNKNOWN.value,
        is_open_to_all_majors=None,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.NEEDS_INFORMATION,
        target_academic_cycle="2026-2027",
        unknown_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.UNKNOWN,
                explanation="Student GPA not provided",
                field="gpa",
                expected_value=3.0,
                actual_value=None,
            )
        ],
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION
    assert res.academic_alignment.level == AlignmentLevel.UNKNOWN
    assert res.testing_readiness.level == ReadinessLevel.UNKNOWN
    assert res.application_readiness.level == ReadinessLevel.NOT_APPLICABLE
    assert res.funding_assessment.funding_classification == FundingClassification.UNKNOWN


def test_adversarial_profile_with_extreme_or_invalid_values(counselor):
    """Profile with negative GPA or nonsensical values handled safely without exceptions."""
    profile = {
        "gpa": -5.0,
        "sat_score": 999999,
        "citizenship_country": "",
        "residence_country": "UNKNOWN_COUNTRY_XYZ",
    }
    opp = MagicMock(
        id="opp-extreme",
        title="Extreme Bounds Opp",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=False,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.INELIGIBLE,
        target_academic_cycle="2026-2027",
        failed_rules=[
            RuleEvaluationResult(
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                status=TriState.NO,
                explanation="GPA -5.0 does not satisfy minimum 3.0",
                field="gpa",
                expected_value=3.0,
                actual_value=-5.0,
            )
        ],
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert len(res.gaps) >= 1


# ==============================================================================
# 2. MISSING OPPORTUNITY ATTRIBUTES & NULL RELATIONS
# ==============================================================================

def test_adversarial_opportunity_all_none_relations(counselor):
    """Opportunity where award, deadlines, sources, and requirements are None or empty."""
    profile = {"gpa": 3.8, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-all-none",
        title=None,
        verification_status=VerificationState.UNVERIFIED.value,
        requires_sat=None,
        requires_act=None,
        is_open_to_all_majors=None,
        official_sources=None,
        deadlines=None,
        application_requirements=None,
        requirements=None,
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.NEEDS_INFORMATION,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res is not None
    assert res.funding_assessment.funding_classification == FundingClassification.UNKNOWN
    assert res.deadline_assessment.deadlines == []


# ==============================================================================
# 3. MALFORMED ELIGIBILITY RULE AST VALIDATION
# ==============================================================================

def test_adversarial_unknown_operator_rejected():
    """Rule with an unrecognized operator raises RuleValidationError."""
    expr = {"op": "SUPER_MATCH", "field": "gpa", "value": 3.5}
    with pytest.raises(RuleValidationError, match="Unknown rule operator"):
        validate_rule_expression(expr)


def test_adversarial_excessive_depth_rejected():
    """Rule expression exceeding MAX_RULE_DEPTH (5) raises RuleValidationError."""
    deep_expr = {"op": "EQ", "field": "gpa", "value": 4.0}
    for _ in range(MAX_RULE_DEPTH + 1):
        deep_expr = {"op": "AND", "operands": [deep_expr, {"op": "EQ", "field": "gpa", "value": 4.0}]}

    with pytest.raises(RuleValidationError, match="exceeds maximum allowed nesting depth"):
        validate_rule_expression(deep_expr)


def test_adversarial_invalid_operand_counts_rejected():
    """Logical operators with invalid operand counts must fail validation."""
    # AND with 1 operand
    with pytest.raises(RuleValidationError, match="must have at least 2 operands"):
        validate_rule_expression({"op": "AND", "operands": [{"op": "EQ", "field": "gpa", "value": 3.5}]})

    # NOT with 2 operands
    with pytest.raises(RuleValidationError, match="must have exactly 1 operand"):
        validate_rule_expression({
            "op": "NOT",
            "operands": [
                {"op": "EQ", "field": "gpa", "value": 3.5},
                {"op": "EQ", "field": "gpa", "value": 3.8},
            ]
        })

    # NOT with 0 operands
    with pytest.raises(RuleValidationError, match="must have exactly 1 operand"):
        validate_rule_expression({"op": "NOT", "operands": []})


def test_adversarial_unsupported_field_rejected():
    """Fields not registered in field allowlist are strictly rejected."""
    expr = {"op": "EQ", "field": "arbitrary_unregistered_field", "value": "xyz"}
    with pytest.raises(RuleValidationError, match="not in the registered field allowlist"):
        validate_rule_expression(expr)


# ==============================================================================
# 4. DUPLICATE DEADLINES AND IMPOSSIBLE DATES
# ==============================================================================

def test_adversarial_duplicate_deadlines_handled_cleanly(counselor):
    """Duplicate identical deadlines on same date do not cause crash or task corruption."""
    profile = {"id": "std-dup"}
    opp = MagicMock(
        id="opp-dup-deadline",
        title="Duplicate Deadline Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2026, 12, 1),
                is_exact_date=True,
                timezone="UTC",
                context_description="Deadline copy 1",
                source_evidence_snippet="Source snippet 1",
            ),
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2026, 12, 1),
                is_exact_date=True,
                timezone="UTC",
                context_description="Deadline copy 2",
                source_evidence_snippet="Source snippet 2",
            ),
        ],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res is not None
    assert len(res.deadline_assessment.deadlines) == 2
    # Both evaluated with same remaining days (30 days)
    assert res.deadline_assessment.deadlines[0].days_remaining == 30
    assert res.deadline_assessment.deadlines[1].days_remaining == 30


def test_adversarial_past_deadline_evaluation(counselor):
    """Deadlines strictly in the past relative to reference_date must have negative days_remaining."""
    profile = {"id": "std-past"}
    opp = MagicMock(
        id="opp-past",
        title="Past Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2026, 1, 1),
                is_exact_date=True,
                timezone="UTC",
                context_description="Past deadline",
                source_evidence_snippet="Past deadline snippet",
            )
        ],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    # 2026-01-01 is before 2026-11-01, remaining days < 0
    assert res.deadline_assessment.deadlines[0].days_remaining < 0


# ==============================================================================
# 5. CONTRADICTORY PROVIDER RULES IN EVALUATOR
# ==============================================================================

def test_adversarial_contradictory_rules_fail_cleanly(evaluator):
    """Mutually contradictory required rules (e.g. gpa >= 3.8 AND gpa <= 2.5) evaluate to NO."""
    student_ctx = {"gpa": 3.0}
    opp_rules = [
        MagicMock(
            rule_id="r1",
            kind=RuleKind.REQUIRED.value,
            expression_json={"op": "GTE", "field": "gpa", "value": 3.8},
            description="Minimum 3.8",
            verification_status=VerificationState.VERIFIED.value,
            academic_cycle="2026-2027",
            source_evidence_snippet="Min 3.8 snippet",
        ),
        MagicMock(
            rule_id="r2",
            kind=RuleKind.REQUIRED.value,
            expression_json={"op": "LTE", "field": "gpa", "value": 2.5},
            description="Maximum 2.5",
            verification_status=VerificationState.VERIFIED.value,
            academic_cycle="2026-2027",
            source_evidence_snippet="Max 2.5 snippet",
        ),
    ]
    res = evaluator.evaluate_rules(
        rules=opp_rules,
        student_profile=student_ctx,
        target_academic_cycle="2026-2027",
        opportunity_academic_cycle="2026-2027",
        verification_status=VerificationState.VERIFIED,
    )
    assert res.status == EligibilityStatus.INELIGIBLE
    assert len(res.failed_rules) >= 1
