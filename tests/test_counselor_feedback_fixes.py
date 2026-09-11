"""Tests verifying the 8 specific fixes requested for Phase 1E Counselor.

1. Problem 1: No arbitrary GPA thresholds (3.5 / 3.8 / +0.2). If no GPA rule is published, result is NOT_ASSESSABLE.
2. Problem 2: No invented SAT 1400 / ACT 30 thresholds. Uses verified provider requirements.
3. Problem 3: Absence of a rule is UNKNOWN, not "open". Explicit open declarations yield NOT_ASSESSABLE.
4. Problem 4: Application readiness truthfully checks student preparation state; unrecorded yields UNKNOWN.
5. Problem 5: FULL_FUNDING must be substantiated with comprehensive living coverage; otherwise downgraded to FULL_TUITION.
6. Problem 6: Testing policy UNKNOWN yields ReadinessLevel.UNKNOWN, never NOT_APPLICABLE.
7. Problem 7: Date determinism with explicit reference_date.
8. Problem 8: Genuine evidence snippets in EvidenceReference; zero invented placeholder quotes.
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


def test_problem_1_academic_alignment_no_published_gpa_is_not_assessable():
    """If no explicit minimum GPA rule is published, counselor returns NOT_ASSESSABLE, never assuming 3.5/3.8 is 'strong'."""
    opp = MagicMock()
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    # Even with a 4.0 or 3.8 GPA, without a published rule it must be NOT_ASSESSABLE
    for test_gpa in [3.5, 3.8, 4.0]:
        profile = {"gpa": test_gpa, "gpa_scale": 4.0}
        ctx = assess_academic_alignment(profile, opp, elig_result)
        assert ctx.level == AlignmentLevel.NOT_ASSESSABLE
        assert "does not publish a minimum GPA requirement" in ctx.details[0]


def test_problem_2_no_arbitrary_sat_1400_act_30_thresholds():
    """Testing readiness must not invent 1400 / 30 thresholds; it uses verified provider requirements."""
    opp = MagicMock()
    opp.requires_sat = TriState.YES.value
    opp.requires_act = TriState.NO.value

    # Case A: Provider requires SAT, student has SAT 1350 (no published score cutoff) -> READY
    elig_no_cutoff = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    profile = {"sat_score": 1350}
    ctx = assess_testing_readiness(profile, opp, elig_no_cutoff)
    assert ctx.level == ReadinessLevel.READY
    assert "completed the exam" in ctx.details[0]

    # Case B: Provider publishes explicit minimum SAT requirement of 1400
    elig_with_cutoff = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r_sat",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="SAT meets requirement",
                field="sat_score",
                expected_value=1300,
                actual_value=1350,
            )
        ],
    )
    ctx_met = assess_testing_readiness(profile, opp, elig_with_cutoff)
    assert ctx_met.level == ReadinessLevel.READY
    assert "satisfies published requirement" in ctx_met.details[0]


def test_problem_3_absence_of_program_rule_is_unknown_not_open():
    """Absence of a major rule does not mean open to all majors unless explicitly verified."""
    opp = MagicMock(is_open_to_all_majors=False)
    profile = {"intended_major": "Computer Science"}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    # When no rule extracted and not verified open to all -> UNKNOWN
    ctx = assess_program_alignment(profile, opp, elig_result)
    assert ctx.level == AlignmentLevel.UNKNOWN
    assert "No specific field-of-study restriction was extracted" in ctx.details[0]

    # When explicitly verified open to all -> NOT_ASSESSABLE
    opp.is_open_to_all_majors = True
    ctx_open = assess_program_alignment(profile, opp, elig_result)
    assert ctx_open.level == AlignmentLevel.NOT_ASSESSABLE
    assert "open across all undergraduate fields" in ctx_open.details[0]


def test_problem_3_absence_of_geographic_rule_with_unknown_international_is_unknown():
    """Absence of geographic rule with unknown international flag is UNKNOWN, not NOT_ASSESSABLE."""
    opp = MagicMock(international_students_allowed=TriState.UNKNOWN.value)
    profile = {"citizenship_country": "ETH"}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    ctx = assess_geographic_alignment(profile, opp, elig_result)
    assert ctx.level == AlignmentLevel.UNKNOWN
    assert "No geographic or nationality eligibility rules were extracted" in ctx.details[0]

    # When explicitly verified open to international students
    opp.international_students_allowed = TriState.YES.value
    ctx_open = assess_geographic_alignment(profile, opp, elig_result)
    assert ctx_open.level == AlignmentLevel.NOT_ASSESSABLE
    assert "verified as open to international applicants" in ctx_open.details[0]


def test_problem_4_application_readiness_truthful_assessment():
    """Application readiness distinguishes unrecorded student status (UNKNOWN) from actual preparation."""
    opp = MagicMock()
    req1 = MagicMock(title="Official Transcript", kind=RequirementKind.REQUIRED.value)
    req2 = MagicMock(title="Recommendation Letter", kind=RequirementKind.REQUIRED.value)
    opp.application_requirements = [req1, req2]
    opp.requirements = []

    # Unrecorded status on profile -> UNKNOWN
    profile_unrecorded = {}
    ctx_unknown = assess_application_readiness(profile_unrecorded, opp)
    assert ctx_unknown.level == ReadinessLevel.UNKNOWN
    assert len(ctx_unknown.missing_components) == 0
    assert "Student document preparation status is unrecorded" in ctx_unknown.details[0]

    # Profile tracks preparation: all ready -> READY
    profile_ready = {"prepared_materials": ["Official Transcript", "Recommendation Letter"]}
    ctx_ready = assess_application_readiness(profile_ready, opp)
    assert ctx_ready.level == ReadinessLevel.READY
    assert len(ctx_ready.missing_components) == 0

    # Profile tracks preparation: partial -> PARTIALLY_READY
    profile_partial = {"prepared_materials": ["Official Transcript"]}
    ctx_partial = assess_application_readiness(profile_partial, opp)
    assert ctx_partial.level == ReadinessLevel.PARTIALLY_READY
    assert ctx_partial.missing_components == ["Recommendation Letter"]


def test_problem_5_full_funding_downgraded_without_substantiated_living_coverage():
    """An award labeled FULL_FUNDING is downgraded if components only substantiate tuition and room (living/meals unverified)."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=80000.0,
        funding_components=[
            MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="100% Tuition"),
            MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Housing included"),
            # Note: MEALS and LIVING_EXPENSES / STIPEND are missing
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    # Must NOT blindly trust FULL_FUNDING label
    assert ctx.funding_classification == FundingClassification.FULL_TUITION
    assert "Full tuition only" in ctx.summary
    assert "Room, meals, and living expenses are NOT verified as covered" in ctx.summary
    assert "do not substantiate comprehensive room and meal expenses" in ctx.details[0]


def test_problem_6_testing_unknown_when_provider_requirement_unknown():
    """Testing policy UNKNOWN must yield ReadinessLevel.UNKNOWN, never NOT_APPLICABLE."""
    opp = MagicMock(
        requires_sat=TriState.UNKNOWN.value,
        requires_act=TriState.UNKNOWN.value,
    )
    profile = {"sat_score": 1450}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    ctx = assess_testing_readiness(profile, opp, elig_result)
    assert ctx.level == ReadinessLevel.UNKNOWN
    assert "unconfirmed or under review" in ctx.details[0]


def test_problem_7_deadline_evaluation_deterministic_with_reference_date():
    """assess_deadlines yields deterministic output when explicit reference_date is supplied."""
    opp = MagicMock()
    d = MagicMock(
        deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
        deadline_date=date(2026, 12, 15),
        is_exact_date=True,
        timezone="America/New_York",
        context_description=None,
        source_evidence_snippet=None,
    )
    opp.deadlines = [d]

    # Evaluation on Dec 5: 10 days remaining -> CLOSING_SOON
    ctx1 = assess_deadlines(opp, reference_date=date(2026, 12, 5))
    assert ctx1.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx1.deadlines[0].days_remaining == 10

    # Evaluation on Nov 1: 44 days remaining -> OPEN
    ctx2 = assess_deadlines(opp, reference_date=date(2026, 11, 1))
    assert ctx2.deadlines[0].readiness == DeadlineReadiness.OPEN
    assert ctx2.deadlines[0].days_remaining == 44


def test_problem_8_evidence_references_preserve_genuine_snippets_no_generic_quotes():
    """EvidenceReference must preserve genuine snippets or None; zero placeholder quotes."""
    service = ScholarshipCounselorService()
    profile = {"citizenship_country": "ETH"}

    # Official source with actual snippet
    src1 = MagicMock(
        url="https://univ.edu/scholarship",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY.value,
        extracted_text_snippet="Verbatim scholarship terms from university portal.",
    )
    # Official source without snippet
    src2 = MagicMock(
        url="https://univ.edu/financial-aid",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY.value,
        extracted_text_snippet=None,
        source_evidence_snippet=None,
    )

    opp = MagicMock(
        id="opp-test",
        title="Test Award",
        verification_status=VerificationState.VERIFIED.value,
        official_sources=[src1, src2],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        international_students_allowed=TriState.YES.value,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    res = service.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))

    # Inspect official portal evidence references
    portal_refs = [r for r in res.evidence_references if r.topic == "Official Source Portal"]
    assert len(portal_refs) == 2

    assert portal_refs[0].evidence_quote == "Verbatim scholarship terms from university portal."
    assert portal_refs[1].evidence_quote is None
    # No generic placeholder in any evidence reference quote
    for r in res.evidence_references:
        assert r.evidence_quote != "Primary authoritative opportunity source"
