"""Property and determinism tests ensuring counselor outputs are 100% reproducible."""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
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


def test_counselor_determinism_across_100_runs():
    service = ScholarshipCounselorService()
    profile = {
        "id": "std-42",
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "intended_degree_level": "BACHELOR",
        "intended_destination_country": "US",
        "gpa": 3.82,
        "gpa_scale": 4.0,
        "sat_score": 1490,
        "intended_major": "Computer Science",
    }
    opp = MagicMock(
        id="opp-99",
        title="Deterministic Grant Program",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.YES.value,
        requires_act=TriState.NO.value,
        official_sources=[],
        deadlines=[
            MagicMock(deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value, deadline_date=date(2027, 1, 15), is_exact_date=True)
        ],
        application_requirements=[
            MagicMock(title="Essay", kind="REQUIRED", source_evidence_snippet="Essay statement")
        ],
        requirements=[],
        award=MagicMock(
            funding_classification=FundingClassification.FULL_TUITION.value,
            is_renewable=TriState.YES.value,
            estimated_annual_value_usd=55000.0,
            funding_components=[
                MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Full tuition")
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
                explanation="GPA meets criteria",
                field="gpa",
                expected_value=3.5,
                actual_value=3.82,
            )
        ],
    )

    ref_date = date(2026, 11, 1)

    # First run (evaluated_at defaults deterministically to midnight UTC of reference_date)
    first_res = service.assess_opportunity(profile, opp, elig, reference_date=ref_date)
    first_dump = first_res.model_dump_json()

    for _ in range(100):
        run_res = service.assess_opportunity(profile, opp, elig, reference_date=ref_date)
        run_dump = run_res.model_dump_json()
        assert run_dump == first_dump

    # Explicit evaluated_at parameter verification
    custom_dt = datetime(2026, 11, 1, 14, 30, 45, tzinfo=timezone.utc)
    res1 = service.assess_opportunity(profile, opp, elig, reference_date=ref_date, evaluated_at=custom_dt)
    res2 = service.assess_opportunity(profile, opp, elig, reference_date=ref_date, evaluated_at=custom_dt)
    assert res1.model_dump_json() == res2.model_dump_json()
    assert res1.evaluated_at == custom_dt
