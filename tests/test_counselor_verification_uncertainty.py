"""Tests for counselor verification transparency and uncertainty warning propagation."""
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import VerificationState
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
)


def test_verified_opportunity_produces_no_verification_warning():
    service = ScholarshipCounselorService()
    profile = {"gpa": 3.8, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-1",
        title="Fully Verified Award",
        verification_status=VerificationState.VERIFIED.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        evaluation_contains_unverified_facts=False,
    )

    assessment = service.assess_opportunity(profile, opp, elig_result)
    assert assessment.verification_context.has_warning is False
    assert assessment.verification_context.evaluation_contains_unverified_facts is False


def test_partially_verified_produces_explicit_warning():
    service = ScholarshipCounselorService()
    profile = {"gpa": 3.8, "citizenship_country": "ETH"}
    opp = MagicMock(
        id="opp-2",
        title="Partially Verified Award",
        verification_status=VerificationState.PARTIALLY_VERIFIED.value,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        evaluation_contains_unverified_facts=True,
    )

    assessment = service.assess_opportunity(profile, opp, elig_result)
    assert assessment.verification_context.has_warning is True
    assert assessment.verification_context.evaluation_contains_unverified_facts is True
    assert any("PARTIALLY_VERIFIED" in w for w in assessment.warnings)
    assert any("PARTIALLY_VERIFIED" in s or "Verify award guidelines" in s for s in assessment.recommended_next_steps)
