"""Tests for Phase 1C verification engine producing all 7 canonical states."""
from datetime import date
import pytest

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    AuthorityTier,
    ConflictStatus,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    LivenessStatus,
    QuarantineReason,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.candidate import (
    CandidateAward,
    CandidateDeadline,
    CandidateEvidence,
    CandidateFundingComponent,
    CandidateOpportunity,
)
from scholarship_intelligence.schemas.verification import SourceLivenessResult
from scholarship_intelligence.verification.engine import VerificationEngine


@pytest.fixture
def base_evidence():
    return CandidateEvidence(
        source_url="https://admissions.clarku.edu/scholarships",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Clark University awards the Global Scholars Program to international students with a minimum 3.5 GPA. Deadline is February 1, 2027. Full tuition provided.",
        content_sha256="hash1234",
    )


def test_engine_state_verified(base_evidence):
    cand = CandidateOpportunity(
        title="Global Scholars Program",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES,
        requires_sat=TriState.NO,
        financial_need_required=TriState.NO,
        award=CandidateAward(
            title="Global Scholars Award",
            funding_classification=FundingClassification.FULL_TUITION,
            components=[
                CandidateFundingComponent(
                    component_type=FundingComponentType.TUITION,
                    percentage_tuition=100.0,
                    evidence=base_evidence,
                )
            ],
            evidence=base_evidence,
        ),
        deadlines=[
            CandidateDeadline(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
                raw_date_text="February 1, 2027",
                deadline_date=date(2027, 2, 1),
                is_exact_date=True,
                evidence=base_evidence,
            )
        ],
        source_evidence=[base_evidence],
    )

    decision = VerificationEngine.evaluate(cand)
    assert decision.overall_state == VerificationState.VERIFIED
    assert decision.can_promote is True
    assert len(decision.conflicts) == 0


def test_engine_state_partially_verified(base_evidence):
    # Full funding claimed, but living components missing
    cand = CandidateOpportunity(
        title="Global Scholars Program",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES,
        requires_sat=TriState.NO,
        financial_need_required=TriState.NO,
        award=CandidateAward(
            title="Global Scholars Award",
            funding_classification=FundingClassification.FULL_FUNDING,
            components=[
                CandidateFundingComponent(
                    component_type=FundingComponentType.TUITION,
                    percentage_tuition=100.0,
                    evidence=base_evidence,
                )
            ],
            evidence=base_evidence,
        ),
        source_evidence=[base_evidence],
    )

    decision = VerificationEngine.evaluate(cand)
    assert decision.overall_state == VerificationState.PARTIALLY_VERIFIED
    assert decision.can_promote is True


def test_engine_state_quarantined_for_review():
    suspicious_ev = CandidateEvidence(
        source_url="https://fake-scholarship.com",
        authority_tier=AuthorityTier.THIRD_PARTY,
        evidence_text="Congratulations! Send 00 via Western Union or wire transfer to guarantee award disbursement.",
        content_sha256="fakehash",
    )
    cand = CandidateOpportunity(
        title="Cash Disbursement Scholarship",
        academic_cycle="2026-2027",
        source_evidence=[suspicious_ev],
    )

    decision = VerificationEngine.evaluate(cand)
    assert decision.overall_state == VerificationState.QUARANTINED_FOR_REVIEW
    assert decision.can_promote is False
    assert QuarantineReason.SUSPICIOUS_PAYMENT_REQUEST in decision.quarantine_reasons


def test_engine_state_source_unavailable(base_evidence):
    cand = CandidateOpportunity(
        title="Global Scholars Program",
        academic_cycle="2026-2027",
        source_evidence=[base_evidence],
    )
    liveness_res = SourceLivenessResult(
        source_url=base_evidence.source_url,
        liveness_status=LivenessStatus.NOT_FOUND,
        http_status=404,
        is_live=False,
    )

    decision = VerificationEngine.evaluate(cand, liveness_result=liveness_res)
    assert decision.overall_state == VerificationState.SOURCE_UNAVAILABLE
    assert decision.can_promote is False


def test_engine_state_outdated():
    old_ev = CandidateEvidence(
        source_url="https://university.edu/scholarships",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="For the academic year 2023-2024, international students received grants.",
        content_sha256="oldhash",
    )
    cand = CandidateOpportunity(
        title="Expired Opportunity",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES,
        source_evidence=[old_ev],
    )

    decision = VerificationEngine.evaluate(cand)
    assert decision.overall_state == VerificationState.OUTDATED
    assert decision.can_promote is False


def test_engine_state_unverified():
    third_party_ev = CandidateEvidence(
        source_url="https://randomblog.com/top-scholarships",
        authority_tier=AuthorityTier.THIRD_PARTY,
        evidence_text="Clark offers a great scholarship for international students.",
        content_sha256="thirdpartyhash",
    )
    cand = CandidateOpportunity(
        title="Blog Mention Opportunity",
        academic_cycle="2026-2027",
        source_evidence=[third_party_ev],
    )

    decision = VerificationEngine.evaluate(cand)
    assert decision.overall_state == VerificationState.UNVERIFIED
    assert decision.can_promote is False
