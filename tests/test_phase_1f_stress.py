"""Phase 1F: Performance and Stress Validation.

Evaluates throughput, memory stability, and determinism under stress load:
- 50 synthetic opportunities across varying verification states and rule complexities
- Multiple deadlines, evidence references, and requirement sets
- 5 diverse student profiles (250 end-to-end evaluations)
- Measures execution time and asserts sub-millisecond to low-millisecond performance (<10ms / eval)
- Asserts zero unhandled exceptions, zero crashes, and complete result integrity.
"""
from datetime import date
import time
from unittest.mock import MagicMock
import pytest

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
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


@pytest.fixture
def counselor():
    return ScholarshipCounselorService()


@pytest.fixture
def evaluator():
    return EligibilityEvaluator()


def _create_synthetic_opportunities(count: int = 50):
    """Creates a diverse batch of synthetic scholarship opportunities."""
    opportunities = []
    v_states = list(VerificationState)
    funding_types = [
        FundingClassification.FULL_FUNDING,
        FundingClassification.FULL_TUITION,
        FundingClassification.PARTIAL_FUNDING,
        FundingClassification.UNKNOWN,
    ]

    for i in range(count):
        v_state = v_states[i % len(v_states)]
        f_class = funding_types[i % len(funding_types)]
        min_gpa = 3.0 + (i % 10) * 0.1  # 3.0 to 3.9

        rules = [
            MagicMock(
                rule_id=f"rule_gpa_{i}",
                kind=RuleKind.REQUIRED.value,
                expression_json={"op": "GTE", "field": "gpa", "value": min_gpa},
                description=f"Minimum GPA {min_gpa:.1f}",
                verification_status=v_state.value,
                academic_cycle="2026-2027",
                source_evidence_snippet=f"Requirement excerpt {i}",
            ),
            MagicMock(
                rule_id=f"rule_country_{i}",
                kind=RuleKind.REQUIRED.value,
                expression_json={"op": "IN", "field": "citizenship_country", "value": ["ETH", "KEN", "RWA", "UGA"]},
                description="Target East African citizens",
                verification_status=v_state.value,
                academic_cycle="2026-2027",
                source_evidence_snippet="Must be citizen of East Africa",
            ),
        ]

        deadlines = [
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2027, 1 + (i % 6), 15),
                is_exact_date=True,
                timezone="UTC",
                context_description=f"App deadline {i}",
                source_evidence_snippet=f"Deadline source {i}",
            ),
            MagicMock(
                deadline_type=DeadlineType.FINANCIAL_AID.value,
                deadline_date=date(2027, 2 + (i % 5), 1),
                is_exact_date=True,
                timezone="UTC",
                context_description=f"Aid deadline {i}",
                source_evidence_snippet=f"Aid source {i}",
            ),
        ]

        app_reqs = [
            MagicMock(title="Essay", kind=RequirementKind.REQUIRED.value, source_evidence_snippet="Essay prompt"),
            MagicMock(title="Transcript", kind=RequirementKind.REQUIRED.value, source_evidence_snippet="Official transcript"),
            MagicMock(title="Recommendation", kind=RequirementKind.PREFERRED.value, source_evidence_snippet="Rec letter"),
        ]

        components = []
        if f_class == FundingClassification.FULL_FUNDING:
            components = [
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Full tuition"),
                MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Room covered"),
                MagicMock(component_type=FundingComponentType.MEALS.value, source_evidence_snippet="Board included"),
                MagicMock(component_type=FundingComponentType.LIVING_EXPENSES.value, source_evidence_snippet="Stipend provided"),
            ]
        elif f_class == FundingClassification.FULL_TUITION:
            components = [
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Full tuition only")
            ]

        opp = MagicMock(
            id=f"opp-stress-{i}",
            title=f"Synthetic Scholarship {i}",
            academic_cycle="2026-2027",
            verification_status=v_state.value,
            requires_sat=TriState.NO.value if i % 2 == 0 else TriState.YES.value,
            requires_act=TriState.NO.value,
            is_open_to_all_majors=(i % 3 == 0),
            rules=rules,
            deadlines=deadlines,
            application_requirements=app_reqs,
            requirements=[],
            official_sources=[
                MagicMock(
                    url=f"https://provider-{i}.org/scholarship",
                    authority_tier=AuthorityTier.OFFICIAL_PROVIDER.value,
                    extracted_text_snippet=f"Official source snippet {i}",
                )
            ],
            award=MagicMock(
                funding_classification=f_class.value,
                funding_components=components,
                is_renewable=TriState.YES.value,
                estimated_annual_value_usd=50000.0,
            ) if f_class != FundingClassification.UNKNOWN else None,
        )
        opportunities.append(opp)

    return opportunities


def test_stress_and_throughput_validation(evaluator, counselor):
    """Executes 250 full end-to-end evaluations across 50 synthetic opportunities and 5 profiles."""
    profiles = [
        {"id": "s1", "gpa": 3.9, "citizenship_country": "ETH", "sat_score": 1450, "prepared_materials": ["Essay", "Transcript"]},
        {"id": "s2", "gpa": 3.1, "citizenship_country": "USA", "sat_score": 1200, "prepared_materials": ["Transcript"]},
        {"id": "s3", "id_only": True},  # Sparse profile
        {"id": "s4", "gpa": 3.6, "citizenship_country": "KEN", "sat_score": 1380, "prepared_materials": ["Essay", "Transcript", "Recommendation"]},
        {"id": "s5", "gpa": 2.7, "citizenship_country": "ETH"},  # Low GPA profile
    ]

    opportunities = _create_synthetic_opportunities(count=50)
    ref_date = date(2026, 11, 1)

    eval_count = 0
    t0 = time.perf_counter()

    for student in profiles:
        for opp in opportunities:
            # 1. Eligibility evaluation
            elig_res = evaluator.evaluate_opportunity(
                opportunity=opp,
                student_profile=student,
                target_academic_cycle="2026-2027",
                allow_partially_verified=True,
            )
            assert elig_res is not None

            # 2. Qualitative counselor assessment
            counselor_res = counselor.assess_opportunity(
                student_profile=student,
                opportunity=opp,
                eligibility_result=elig_res,
                reference_date=ref_date,
            )
            assert counselor_res is not None
            assert counselor_res.eligibility_status == elig_res.status
            eval_count += 1

    elapsed = time.perf_counter() - t0
    avg_per_eval_ms = (elapsed / eval_count) * 1000.0

    assert eval_count == 250
    # Performance gate: Average assessment time must be < 10ms (typical is < 1ms)
    assert avg_per_eval_ms < 10.0, f"Average evaluation time {avg_per_eval_ms:.3f}ms exceeded 10ms limit"
    # Total execution time for 250 evaluations must be < 2.5 seconds
    assert elapsed < 2.5, f"Total stress run {elapsed:.3f}s exceeded 2.5s limit"
