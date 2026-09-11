"""Phase 1F: Contract and Verification Gating Tests.

Validates:
- Phase 1D -> 1E Contract: Phase 1E preserves Phase 1D eligibility status across
  all 6 statuses: ELIGIBLE, INELIGIBLE, NEEDS_INFORMATION, GATED_UNVERIFIED,
  NEEDS_REVIEW, OUTDATED_CYCLE. The counselor NEVER overrides the engine's verdict.
- Phase 1C Verification Gating: Every verification state (VERIFIED, PARTIALLY_VERIFIED,
  CONFLICTING, OUTDATED, UNVERIFIED, SOURCE_UNAVAILABLE, QUARANTINED_FOR_REVIEW)
  is surfaced transparently in counselor output and never treated as silently trustworthy.
"""
from datetime import date
from unittest.mock import MagicMock
import pytest

from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
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
# 1. PHASE 1D -> 1E CONTRACT PRESERVATION ACROSS ALL 6 STATUSES
# ==============================================================================

@pytest.mark.parametrize(
    "phase_1d_status",
    [
        EligibilityStatus.ELIGIBLE,
        EligibilityStatus.INELIGIBLE,
        EligibilityStatus.NEEDS_INFORMATION,
        EligibilityStatus.GATED_UNVERIFIED,
        EligibilityStatus.NEEDS_REVIEW,
        EligibilityStatus.OUTDATED_CYCLE,
    ],
)
def test_contract_phase_1e_never_overrides_phase_1d_status(counselor, phase_1d_status):
    """Phase 1E counselor strictly adopts Phase 1D status without overriding or mutating."""
    profile = {"gpa": 3.9, "citizenship_country": "ETH"}
    opp = MagicMock(
        id=f"opp-contract-{phase_1d_status.value}",
        title=f"Contract Test {phase_1d_status.value}",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=phase_1d_status,
        target_academic_cycle="2026-2027",
        opportunity_academic_cycle="2026-2027",
        verification_status=VerificationState.VERIFIED,
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.eligibility_status == phase_1d_status, (
        f"Counselor altered Phase 1D status from {phase_1d_status} to {res.eligibility_status}"
    )


# ==============================================================================
# 2. PHASE 1C VERIFICATION STATE GATING AND WARNINGS
# ==============================================================================

@pytest.mark.parametrize(
    "v_state, expected_warning, expected_contains_unverified",
    [
        (VerificationState.VERIFIED, False, False),
        (VerificationState.PARTIALLY_VERIFIED, True, True),
        (VerificationState.CONFLICTING, True, False),
        (VerificationState.OUTDATED, True, False),
        (VerificationState.UNVERIFIED, True, False),
        (VerificationState.SOURCE_UNAVAILABLE, True, False),
        (VerificationState.QUARANTINED_FOR_REVIEW, True, False),
    ],
)
def test_verification_states_surfaced_with_appropriate_gating_and_warnings(
    counselor, v_state, expected_warning, expected_contains_unverified
):
    """Every Phase 1C verification state is handled transparently with mandatory warnings when unverified/conflicting."""
    profile = {"gpa": 3.9, "citizenship_country": "ETH"}
    opp = MagicMock(
        id=f"opp-v-{v_state.value}",
        title=f"Verification Test {v_state.value}",
        verification_status=v_state.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.GATED_UNVERIFIED if v_state in {
            VerificationState.UNVERIFIED,
            VerificationState.CONFLICTING,
            VerificationState.QUARANTINED_FOR_REVIEW,
            VerificationState.SOURCE_UNAVAILABLE,
        } else EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        verification_status=v_state,
        evaluation_contains_unverified_facts=expected_contains_unverified,
    )

    res = counselor.assess_opportunity(profile, opp, elig, reference_date=date(2026, 11, 1))
    assert res.verification_context.verification_status == v_state
    assert res.verification_context.has_warning == expected_warning
    assert res.verification_context.evaluation_contains_unverified_facts == expected_contains_unverified

    if expected_warning:
        assert res.verification_context.warning_message is not None
        assert len(res.warnings) >= 1
        assert any(res.verification_context.warning_message in w for w in res.warnings)


def test_quarantined_and_unverified_never_pass_evaluator(evaluator):
    """Evaluator gates UNVERIFIED, CONFLICTING, and QUARANTINED opportunities by default."""
    student = {"gpa": 3.9}

    for dangerous_state in [
        VerificationState.UNVERIFIED,
        VerificationState.CONFLICTING,
        VerificationState.QUARANTINED_FOR_REVIEW,
        VerificationState.SOURCE_UNAVAILABLE,
        VerificationState.OUTDATED,
    ]:
        opp = MagicMock(
            id=f"opp-gate-{dangerous_state.value}",
            title="Gated Opp",
            academic_cycle="2026-2027",
            verification_status=dangerous_state.value,
            rules=[],
        )
        res = evaluator.evaluate_opportunity(
            opportunity=opp,
            student_profile=student,
            target_academic_cycle="2026-2027",
            allow_partially_verified=False,
        )
        assert res.is_gated is True
        assert res.status != EligibilityStatus.ELIGIBLE
        assert res.status in {EligibilityStatus.GATED_UNVERIFIED, EligibilityStatus.NEEDS_REVIEW}
