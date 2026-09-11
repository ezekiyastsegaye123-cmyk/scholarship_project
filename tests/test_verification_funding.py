"""Tests for funding verification, decomposition, and full tuition vs full funding constraints."""
import pytest
from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    AuthorityTier,
    FundingClassification,
    FundingComponentType,
    VerificationState,
)
from scholarship_intelligence.schemas.candidate import (
    CandidateAward,
    CandidateEvidence,
    CandidateFundingComponent,
)
from scholarship_intelligence.verification.fact_verifier import FactVerifier


def test_full_tuition_does_not_equal_full_funding():
    """Mandatory rule: Full tuition coverage alone cannot be marked VERIFIED for FULL_FUNDING."""
    ev = CandidateEvidence(
        source_url="https://admissions.clarku.edu/aid",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Full tuition coverage provided for four years.",
        content_sha256="tuitionhash",
    )
    # Candidate erroneously categorized full tuition as FULL_FUNDING
    award = CandidateAward(
        title="Clark Presidential Scholarship",
        funding_classification=FundingClassification.FULL_FUNDING,
        components=[
            CandidateFundingComponent(
                component_type=FundingComponentType.TUITION,
                percentage_tuition=100.0,
                evidence=ev,
            )
        ],
        evidence=ev,
    )

    results = FactVerifier.verify_funding_components(award)
    class_res = next(r for r in results if r.field_name == "funding_classification")
    # Must be downgraded to PARTIALLY_VERIFIED due to lack of living/room/board support
    assert class_res.verification_state == VerificationState.PARTIALLY_VERIFIED
    assert "FULL_FUNDING claimed, but living expenses/room/board are not verified" in class_res.notes


def test_full_funding_with_living_expenses_verified():
    ev_tuition = CandidateEvidence(
        source_url="https://berea.edu/aid",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="100% Tuition Promise Scholarship for four years.",
        content_sha256="hash1",
    )
    ev_room = CandidateEvidence(
        source_url="https://berea.edu/aid",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Labor program covers room and board expenses.",
        content_sha256="hash2",
    )
    award = CandidateAward(
        title="Berea Full Coverage Package",
        funding_classification=FundingClassification.FULL_FUNDING,
        components=[
            CandidateFundingComponent(
                component_type=FundingComponentType.TUITION,
                percentage_tuition=100.0,
                evidence=ev_tuition,
            ),
            CandidateFundingComponent(
                component_type=FundingComponentType.ROOM,
                amount_min=5000.0,
                amount_max=5000.0,
                evidence=ev_room,
            ),
        ],
        evidence=ev_tuition,
    )

    results = FactVerifier.verify_funding_components(award)
    class_res = next(r for r in results if r.field_name == "funding_classification")
    assert class_res.verification_state == VerificationState.VERIFIED
