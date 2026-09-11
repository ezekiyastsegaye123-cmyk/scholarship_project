"""Golden test cases for Phase 1E qualitative counselor scenarios (Cases A through H)."""
from datetime import date
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    RuleKind,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


@pytest.fixture
def service():
    return ScholarshipCounselorService()


def test_golden_case_a_strong_alignment(service):
    """Case A: Eligible student with complete verified data."""
    profile = {
        "id": "std-1",
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "gpa": 3.9,
        "gpa_scale": 4.0,
        "sat_score": 1500,
        "intended_major": "Computer Science",
    }
    opp = MagicMock(
        id="opp-1",
        title="Merit Leadership Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        official_sources=[
            MagicMock(source_url="https://univ.edu/scholarship", authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY)
        ],
        deadlines=[
            MagicMock(deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value, deadline_date=date(2027, 1, 15), is_exact_date=True)
        ],
        application_requirements=[
            MagicMock(title="Essay", kind="REQUIRED", source_evidence_snippet="Personal statement")
        ],
        requirements=[],
        award=MagicMock(
            funding_classification=FundingClassification.FULL_FUNDING.value,
            is_renewable=TriState.YES.value,
            estimated_annual_value_usd=80000.0,
            funding_components=[
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Tuition"),
                MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Housing"),
            ],
        ),
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="GPA meets requirement",
                field="gpa",
                expected_value=3.5,
                actual_value=3.9,
                evidence_snippet="Minimum GPA 3.5",
            ),
            RuleEvaluationResult(
                rule_id="r2",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="Citizenship eligible",
                field="citizenship_country",
                expected_value=["ETH", "KEN"],
                actual_value="ETH",
            ),
        ],
    )

    res = service.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.ELIGIBLE
    assert res.academic_alignment.level == AlignmentLevel.STRONG
    assert res.geographic_alignment.level == AlignmentLevel.STRONG
    assert res.testing_readiness.level == ReadinessLevel.READY
    assert len(res.strengths) >= 3
    assert len(res.gaps) == 0


def test_golden_case_b_ineligible(service):
    """Case B: Student fails a mandatory published requirement."""
    profile = {"gpa": 3.1, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-2",
        title="High Honors Award",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
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
                explanation="Requires minimum GPA of 3.5, student has 3.1",
                field="gpa",
                expected_value=3.5,
                actual_value=3.1,
            )
        ],
    )

    res = service.assess_opportunity(profile, opp, elig)
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert res.academic_alignment.level == AlignmentLevel.LIMITED
    assert any("Unmet mandatory rule" in g for g in res.gaps)
    assert any("not advised" in w.lower() for w in res.warnings)
    assert any("alternative" in s.lower() for s in res.recommended_next_steps)


def test_golden_case_c_missing_information(service):
    """Case C: Student lacks GPA -> NEEDS_INFORMATION (never INELIGIBLE)."""
    profile = {"citizenship_country": "ETH"}  # Missing GPA
    opp = MagicMock(
        id="opp-3",
        title="Need-Aware Grant",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
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
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                status=TriState.UNKNOWN,
                explanation="Requires GPA >= 3.5, student GPA not provided",
                field="gpa",
                expected_value=3.5,
            )
        ],
    )

    res = service.assess_opportunity(profile, opp, elig)
    assert res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION
    assert res.academic_alignment.level == AlignmentLevel.UNKNOWN
    assert any("missing profile facts" in w.lower() for w in res.warnings)
    assert any("complete your profile" in s.lower() for s in res.recommended_next_steps)


def test_golden_case_d_conflicting_evidence(service):
    """Case D: Disagreeing official sources -> NEEDS_REVIEW with explicit warning."""
    profile = {"gpa": 3.8, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-4",
        title="Contested Criteria Scholarship",
        verification_status=VerificationState.CONFLICTING.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.NEEDS_REVIEW,
        target_academic_cycle="2026-2027",
        conflicting_rules=[
            RuleEvaluationResult(
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                status=TriState.CONFLICTING,
                explanation="Contradictory GPA criteria across sources",
            )
        ],
    )

    res = service.assess_opportunity(profile, opp, elig)
    assert res.eligibility_status == EligibilityStatus.NEEDS_REVIEW
    assert res.verification_context.has_warning is True
    assert any("Contradictory evidence" in w for w in res.warnings)


def test_golden_case_e_partially_verified(service):
    """Case E: Partially verified opportunity evaluation allowed with visible warning."""
    profile = {"gpa": 3.8, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-5",
        title="Draft Directory Grant",
        verification_status=VerificationState.PARTIALLY_VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        evaluation_contains_unverified_facts=True,
    )

    res = service.assess_opportunity(profile, opp, elig)
    assert res.verification_context.evaluation_contains_unverified_facts is True
    assert any("PARTIALLY_VERIFIED" in w for w in res.warnings)


def test_golden_case_f_funding_ambiguity(service):
    """Case F: Full tuition verified but living expenses unstated -> never claims 'Fully funded'."""
    opp = MagicMock(
        id="opp-6",
        title="Presidential Tuition Fellowship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=MagicMock(
            funding_classification=FundingClassification.FULL_TUITION.value,
            is_renewable=TriState.YES.value,
            estimated_annual_value_usd=62000.0,
            funding_components=[
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="100% tuition")
            ],
        ),
    )
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    res = service.assess_opportunity({}, opp, elig)
    assert res.funding_assessment.funding_classification == FundingClassification.FULL_TUITION
    assert "Full tuition only" in res.funding_assessment.summary
    assert "Fully funded" not in res.funding_assessment.summary
    assert any("does not include room" in w.lower() for w in res.warnings)


def test_golden_case_g_multiple_deadlines(service):
    """Case G: Application deadline and financial aid deadline are both preserved."""
    opp = MagicMock(
        id="opp-7",
        title="Dual Deadline Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[
            MagicMock(
                deadline_type=DeadlineType.UNIVERSITY_APPLICATION.value,
                deadline_date=date(2026, 12, 1),
                is_exact_date=True,
            ),
            MagicMock(
                deadline_type=DeadlineType.FINANCIAL_AID.value,
                deadline_date=date(2027, 2, 1),
                is_exact_date=True,
            ),
        ],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    res = service.assess_opportunity({}, opp, elig, reference_date=date(2026, 11, 1))
    assert len(res.deadline_assessment.deadlines) == 2
    types_found = {d.deadline_type for d in res.deadline_assessment.deadlines}
    assert DeadlineType.UNIVERSITY_APPLICATION in types_found
    assert DeadlineType.FINANCIAL_AID in types_found


def test_golden_case_h_no_competitiveness_inference(service):
    """Case H: Counselor provides qualitative alignment without fake numerical probability."""
    profile = {"gpa": 4.0, "sat_score": 1590, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-8",
        title="Top Scholar Program",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    res = service.assess_opportunity(profile, opp, elig)
    # Check that result model has NO score attributes
    assert not hasattr(res, "competitiveness_score")
    assert not hasattr(res, "acceptance_probability")
    assert not hasattr(res, "fit_score")
    assert not hasattr(res, "match_score")
    assert not hasattr(res, "ranking")

    # Serialize to dict and ensure no probability or score keys exist
    dump = res.model_dump()
    forbidden = ["probability", "fit_score", "match_score", "competitiveness_score", "ranking"]
    for k in dump.keys():
        for f in forbidden:
            assert f not in k.lower()
