"""Phase 1F Benchmark Suite — Benchmarks A through V.

Validates end-to-end correctness, epistemic safety, deterministic evaluations,
provenance preservation, and absence of arbitrary heuristics across the entire Phase 1 pipeline.
"""
from datetime import date
from unittest.mock import MagicMock
import pytest

from scholarship_intelligence.counselor.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)
from scholarship_intelligence.counselor.rules import (
    assess_academic_alignment,
    assess_application_readiness,
    assess_deadlines,
    assess_funding,
    assess_geographic_alignment,
    assess_program_alignment,
    assess_testing_readiness,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    RequirementKind,
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
def counselor():
    return ScholarshipCounselorService()


# --- Benchmark A: Fully Verified Eligible Opportunity ---
def test_benchmark_a_fully_verified_eligible(counselor):
    """Benchmark A: Eligible student with fully verified opportunity produces ELIGIBLE with 0 verification warnings."""
    profile = {
        "id": "std-a",
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "gpa": 3.9,
        "gpa_scale": 4.0,
        "sat_score": 1450,
        "intended_major": "Computer Science",
        "prepared_materials": ["Essay", "Transcript"],
    }
    opp = MagicMock(
        id="opp-a",
        title="Full International Merit Scholarship",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[
            MagicMock(
                url="https://univ.edu/merit",
                authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY.value,
                extracted_text_snippet="Official verified award guidelines.",
            )
        ],
        deadlines=[
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2027, 2, 1),
                is_exact_date=True,
                timezone="America/New_York",
                context_description="Application deadline",
                source_evidence_snippet="Deadline Feb 1",
            )
        ],
        application_requirements=[
            MagicMock(title="Essay", kind=RequirementKind.REQUIRED.value, source_evidence_snippet="Essay prompt"),
            MagicMock(title="Transcript", kind=RequirementKind.REQUIRED.value, source_evidence_snippet="Official transcript"),
        ],
        requirements=[],
        award=MagicMock(
            funding_classification=FundingClassification.FULL_FUNDING.value,
            is_renewable=TriState.YES.value,
            estimated_annual_value_usd=85000.0,
            funding_components=[
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="100% Tuition"),
                MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Room covered"),
                MagicMock(component_type=FundingComponentType.MEALS.value, source_evidence_snippet="Meal plan included"),
                MagicMock(component_type=FundingComponentType.LIVING_EXPENSES.value, source_evidence_snippet="Living stipend"),
            ],
        ),
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="GPA satisfies minimum 3.5",
                field="gpa",
                expected_value=3.5,
                actual_value=3.9,
            ),
            RuleEvaluationResult(
                rule_id="r_geo",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="Eligible country",
                field="citizenship_country",
                expected_value=["ETH", "KEN"],
                actual_value="ETH",
            ),
        ],
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.ELIGIBLE
    assert res.verification_context.has_warning is False
    assert res.verification_context.evaluation_contains_unverified_facts is False
    assert res.funding_assessment.funding_classification == FundingClassification.FULL_FUNDING
    assert res.application_readiness.level == ReadinessLevel.READY
    assert len(res.strengths) >= 3
    assert len(res.gaps) == 0


# --- Benchmark B: Hard Ineligible Student ---
def test_benchmark_b_hard_ineligible_student(counselor):
    """Benchmark B: Student fails verified GPA requirement -> INELIGIBLE, identifies failure without inventing others."""
    profile = {"gpa": 2.9, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-b",
        title="High Honor Scholarship",
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
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.NO,
                explanation="Requires minimum GPA 3.5, student has 2.9",
                field="gpa",
                expected_value=3.5,
                actual_value=2.9,
            )
        ],
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert res.academic_alignment.level == AlignmentLevel.LIMITED
    assert len(res.gaps) == 2  # Unmet mandatory rule and academic GPA falls below minimum
    assert any("Requires minimum GPA 3.5" in g for g in res.gaps)
    assert any("below the published minimum requirement" in d for d in res.academic_alignment.details)


# --- Benchmark C: Sparse Student Profile ---
def test_benchmark_c_sparse_profile_preserves_unknown(counselor):
    """Benchmark C: Missing student facts yield NEEDS_INFORMATION, UNKNOWN, NOT_ASSESSABLE; never converted to NO or INELIGIBLE."""
    profile = {"id": "std-sparse"}  # No GPA, major, testing, or citizenship
    opp = MagicMock(
        id="opp-c",
        title="General Opportunity",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
        is_open_to_all_majors=True,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.NEEDS_INFORMATION,
        target_academic_cycle="2026-2027",
        unknown_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.UNKNOWN,
                explanation="GPA is required but missing",
                field="gpa",
                expected_value=3.0,
            )
        ],
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION
    assert res.academic_alignment.level == AlignmentLevel.UNKNOWN
    assert res.testing_readiness.level == ReadinessLevel.NEEDS_PREPARATION  # Tests required, no score on file
    assert res.program_alignment.level == AlignmentLevel.NOT_ASSESSABLE  # Verified open to all majors
    assert len(res.unknowns) >= 1
    assert not any("INELIGIBLE" in str(s) for s in res.strengths)


# --- Benchmark D: No Published GPA Requirement ---
def test_benchmark_d_no_published_gpa_is_not_assessable():
    """Benchmark D: Multiple GPAs (3.0, 3.5, 3.8, 4.0) all yield NOT_ASSESSABLE when no GPA rule exists."""
    opp = MagicMock()
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    for test_gpa in [3.0, 3.5, 3.8, 4.0]:
        profile = {"gpa": test_gpa, "gpa_scale": 4.0}
        ctx = assess_academic_alignment(profile, opp, elig)
        assert ctx.level == AlignmentLevel.NOT_ASSESSABLE
        assert "does not publish a minimum GPA requirement" in ctx.details[0]


# --- Benchmark E: Testing Policy UNKNOWN ---
def test_benchmark_e_testing_policy_unknown():
    """Benchmark E: When provider testing requirements are UNKNOWN, readiness is UNKNOWN (never NOT_APPLICABLE)."""
    opp = MagicMock(requires_sat=TriState.UNKNOWN.value, requires_act=TriState.UNKNOWN.value)
    profile = {"sat_score": 1500}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig)
    assert ctx.level == ReadinessLevel.UNKNOWN
    assert "requirements are unconfirmed or under review" in ctx.details[0]


# --- Benchmark F: Testing Explicitly Not Required ---
def test_benchmark_f_testing_explicitly_not_required():
    """Benchmark F: When provider testing is confirmed NO, readiness is NOT_APPLICABLE (proving UNKNOWN != NO)."""
    opp = MagicMock(requires_sat=TriState.NO.value, requires_act=TriState.NO.value)
    profile = {}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig)
    assert ctx.level == ReadinessLevel.NOT_APPLICABLE
    assert "confirmed not required" in ctx.details[0]


# --- Benchmark G: Required Test Without Published Score Threshold ---
def test_benchmark_g_required_test_without_score_threshold():
    """Benchmark G: Provider requires test without score cutoff; student with SAT 1350 is READY (no invented 1400 cutoff)."""
    opp = MagicMock(requires_sat=TriState.YES.value, requires_act=TriState.NO.value)
    profile = {"sat_score": 1350}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig)
    assert ctx.level == ReadinessLevel.READY
    assert "completed the exam" in ctx.details[0]


# --- Benchmark H: Explicit Published Score Threshold ---
def test_benchmark_h_explicit_published_score_threshold():
    """Benchmark H: Evaluates strictly against provider's published minimum score threshold."""
    opp = MagicMock(requires_sat=TriState.YES.value, requires_act=TriState.NO.value)

    # Sub-case 1: Student score below verified requirement (SAT 1350 vs min 1400)
    profile_below = {"sat_score": 1350}
    elig_below = EligibilityEvaluationResult(
        status=EligibilityStatus.INELIGIBLE,
        target_academic_cycle="2026-2027",
        failed_rules=[
            RuleEvaluationResult(
                rule_id="r_sat",
                kind=RuleKind.REQUIRED,
                status=TriState.NO,
                explanation="Requires minimum SAT 1400",
                field="sat_score",
                expected_value=1400,
                actual_value=1350,
            )
        ],
    )
    ctx_below = assess_testing_readiness(profile_below, opp, elig_below)
    assert ctx_below.level == ReadinessLevel.NEEDS_PREPARATION

    # Sub-case 2: Student score meets verified requirement (SAT 1400 vs min 1400)
    profile_met = {"sat_score": 1400}
    elig_met = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r_sat",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="SAT satisfies minimum 1400",
                field="sat_score",
                expected_value=1400,
                actual_value=1400,
            )
        ],
    )
    ctx_met = assess_testing_readiness(profile_met, opp, elig_met)
    assert ctx_met.level == ReadinessLevel.READY


# --- Benchmark I: Geographic UNKNOWN ---
def test_benchmark_i_geographic_unknown():
    """Benchmark I: No geographic rule and international status UNKNOWN yields UNKNOWN (never NOT_ASSESSABLE)."""
    opp = MagicMock(international_students_allowed=TriState.UNKNOWN.value)
    profile = {"citizenship_country": "ETH"}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_geographic_alignment(profile, opp, elig)
    assert ctx.level == AlignmentLevel.UNKNOWN
    assert "No geographic or nationality eligibility rules were extracted" in ctx.details[0]


# --- Benchmark J: Explicit International Eligibility ---
def test_benchmark_j_explicit_international_eligibility():
    """Benchmark J: Provider verifies international_students_allowed = YES yields NOT_ASSESSABLE for regional criteria."""
    opp = MagicMock(international_students_allowed=TriState.YES.value)
    profile = {"citizenship_country": "ETH"}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_geographic_alignment(profile, opp, elig)
    assert ctx.level == AlignmentLevel.NOT_ASSESSABLE
    assert "verified as open to international applicants without regional restrictions" in ctx.details[0]


# --- Benchmark K: Program Restriction UNKNOWN ---
def test_benchmark_k_program_restriction_unknown():
    """Benchmark K: No major rule and not verified open to all yields UNKNOWN (never open to all)."""
    opp = MagicMock(is_open_to_all_majors=False)
    profile = {"intended_major": "Mechanical Engineering"}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_program_alignment(profile, opp, elig)
    assert ctx.level == AlignmentLevel.UNKNOWN
    assert "No specific field-of-study restriction was extracted" in ctx.details[0]


# --- Benchmark L: Explicit All-Major Opportunity ---
def test_benchmark_l_explicit_all_major_opportunity():
    """Benchmark L: Provider explicitly verifies is_open_to_all_majors = True yields NOT_ASSESSABLE."""
    opp = MagicMock(is_open_to_all_majors=True)
    profile = {"intended_major": "Mechanical Engineering"}
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_program_alignment(profile, opp, elig)
    assert ctx.level == AlignmentLevel.NOT_ASSESSABLE
    assert "explicitly published as open across all undergraduate fields" in ctx.details[0]


# --- Benchmark M: Full Tuition Only ---
def test_benchmark_m_full_tuition_only():
    """Benchmark M: Award covers tuition only; living support unverified yields FULL_TUITION (never FULL_FUNDING)."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_TUITION.value,
        is_renewable=TriState.YES.value,
        funding_components=[
            MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="100% Tuition"),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_TUITION
    assert "Full tuition only" in ctx.summary
    assert "Room, meals, and living expenses are NOT verified as covered" in ctx.summary


# --- Benchmark N: Fully Substantiated Funding ---
def test_benchmark_n_fully_substantiated_funding():
    """Benchmark N: Components substantiate tuition, room, and meals (or living stipend) -> FULL_FUNDING."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        funding_components=[
            MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Tuition"),
            MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Room"),
            MagicMock(component_type=FundingComponentType.MEALS.value, source_evidence_snippet="Board"),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_FUNDING
    assert "Full funding" in ctx.summary
    assert "tuition as well as living, room, and board" in ctx.summary


# --- Benchmark O: Application Preparation UNKNOWN ---
def test_benchmark_o_application_preparation_unknown():
    """Benchmark O: Required documents exist, but student profile has no preparation state -> UNKNOWN."""
    opp = MagicMock()
    req = MagicMock(title="Recommendation Letter", kind=RequirementKind.REQUIRED.value)
    opp.application_requirements = [req]
    opp.requirements = []

    profile = {}  # No prepared_materials key
    ctx = assess_application_readiness(profile, opp)
    assert ctx.level == ReadinessLevel.UNKNOWN
    assert "Student document preparation status is unrecorded" in ctx.details[0]


# --- Benchmark P: Application Preparation Complete ---
def test_benchmark_p_application_preparation_complete():
    """Benchmark P: Student has prepared all required documents -> READY."""
    opp = MagicMock()
    req1 = MagicMock(title="Essay", kind=RequirementKind.REQUIRED.value)
    req2 = MagicMock(title="Transcript", kind=RequirementKind.REQUIRED.value)
    opp.application_requirements = [req1, req2]
    opp.requirements = []

    profile = {"prepared_materials": ["Essay", "Transcript"]}
    ctx = assess_application_readiness(profile, opp)
    assert ctx.level == ReadinessLevel.READY
    assert len(ctx.missing_components) == 0


# --- Benchmark Q: Partial Preparation ---
def test_benchmark_q_partial_preparation():
    """Benchmark Q: Student has prepared a subset of required documents -> PARTIALLY_READY with missing item identified."""
    opp = MagicMock()
    req1 = MagicMock(title="Essay", kind=RequirementKind.REQUIRED.value)
    req2 = MagicMock(title="Recommendation Letter", kind=RequirementKind.REQUIRED.value)
    opp.application_requirements = [req1, req2]
    opp.requirements = []

    profile = {"prepared_materials": ["Essay"]}
    ctx = assess_application_readiness(profile, opp)
    assert ctx.level == ReadinessLevel.PARTIALLY_READY
    assert ctx.missing_components == ["Recommendation Letter"]


# --- Benchmark R: Multiple Deadlines Preserved Independently ---
def test_benchmark_r_multiple_deadlines_preserved():
    """Benchmark R: Distinct application and financial aid deadlines are preserved independently."""
    opp = MagicMock()
    d1 = MagicMock(
        deadline_type=DeadlineType.UNIVERSITY_APPLICATION.value,
        deadline_date=date(2027, 1, 1),
        is_exact_date=True,
    )
    d2 = MagicMock(
        deadline_type=DeadlineType.FINANCIAL_AID.value,
        deadline_date=date(2027, 2, 1),
        is_exact_date=True,
    )
    opp.deadlines = [d1, d2]

    ctx = assess_deadlines(opp, reference_date=date(2026, 11, 1))
    assert len(ctx.deadlines) == 2
    types = [item.deadline_type for item in ctx.deadlines]
    assert DeadlineType.UNIVERSITY_APPLICATION in types
    assert DeadlineType.FINANCIAL_AID in types


# --- Benchmark S: Deterministic Deadline Evaluation with Explicit Reference Date ---
def test_benchmark_s_deterministic_deadlines():
    """Benchmark S: Deadline readiness transitions deterministically across exact reference date offsets."""
    opp = MagicMock()
    d = MagicMock(
        deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
        deadline_date=date(2026, 12, 1),
        is_exact_date=True,
    )
    opp.deadlines = [d]

    # Exactly 0 days remaining (due today) -> CLOSING_SOON
    ctx_0 = assess_deadlines(opp, reference_date=date(2026, 12, 1))
    assert ctx_0.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx_0.deadlines[0].days_remaining == 0

    # 1 day remaining -> CLOSING_SOON
    ctx_1 = assess_deadlines(opp, reference_date=date(2026, 11, 30))
    assert ctx_1.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx_1.deadlines[0].days_remaining == 1

    # 14 days remaining -> CLOSING_SOON (boundary)
    ctx_14 = assess_deadlines(opp, reference_date=date(2026, 11, 17))
    assert ctx_14.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx_14.deadlines[0].days_remaining == 14

    # 15 days remaining -> OPEN (boundary)
    ctx_15 = assess_deadlines(opp, reference_date=date(2026, 11, 16))
    assert ctx_15.deadlines[0].readiness == DeadlineReadiness.OPEN
    assert ctx_15.deadlines[0].days_remaining == 15

    # 30 days remaining -> OPEN
    ctx_30 = assess_deadlines(opp, reference_date=date(2026, 11, 1))
    assert ctx_30.deadlines[0].readiness == DeadlineReadiness.OPEN
    assert ctx_30.deadlines[0].days_remaining == 30


# --- Benchmark T: Partially Verified Opportunity ---
def test_benchmark_t_partially_verified_warning(counselor):
    """Benchmark T: PARTIALLY_VERIFIED opportunity sets evaluation_contains_unverified_facts = True with warning."""
    profile = {"citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-part",
        title="Partially Verified Award",
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
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.verification_context.evaluation_contains_unverified_facts is True
    assert res.verification_context.has_warning is True
    assert any("PARTIALLY_VERIFIED" in w for w in res.warnings)


# --- Benchmark U: Conflicting Source Facts ---
def test_benchmark_u_conflicting_source_facts(counselor):
    """Benchmark U: CONFLICTING verification state is preserved; counselor warns without fabricating a resolution."""
    profile = {"citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-conflict",
        title="Conflicted Award",
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
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.verification_context.verification_status == VerificationState.CONFLICTING
    assert res.verification_context.has_warning is True
    assert any("Contradictory evidence" in w or "counselor review" in w for w in res.warnings)


# --- Benchmark V: Source Evidence Integrity ---
def test_benchmark_v_source_evidence_integrity(counselor):
    """Benchmark V: Every factual evidence reference contains genuine snippets or None; zero generic placeholder text."""
    profile = {"citizenship_country": "ETH"}
    src_real = MagicMock(
        url="https://univ.edu/guidelines",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY.value,
        extracted_text_snippet="Verbatim text from source.",
    )
    src_none = MagicMock(
        url="https://univ.edu/contact",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY.value,
        extracted_text_snippet=None,
        source_evidence_snippet=None,
    )
    opp = MagicMock(
        id="opp-v",
        title="Evidence Test Award",
        verification_status=VerificationState.VERIFIED.value,
        official_sources=[src_real, src_none],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
    )
    elig = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    for ref in res.evidence_references:
        assert ref.evidence_quote != "Primary authoritative opportunity source"
        if ref.source_url == "https://univ.edu/guidelines":
            assert ref.evidence_quote == "Verbatim text from source."
        elif ref.source_url == "https://univ.edu/contact":
            assert ref.evidence_quote is None
