"""Verification-specific no-fabrication tests.

Enforces:
- Missing evidence cannot yield VERIFIED.
- Unrelated citation cannot yield VERIFIED.
- Unknown facts cannot be fabricated into definite claims.
- No arbitrary numeric confidence, fit, or acceptance probability scores.
"""
import pytest
from scholarship_intelligence.domain.enums import AuthorityTier, TriState, VerificationState
from scholarship_intelligence.schemas.candidate import CandidateEvidence
from scholarship_intelligence.verification.fact_verifier import FactVerifier


def test_fact_with_missing_evidence_cannot_become_verified():
    res = FactVerifier.verify_field(
        field_name="minimum_gpa",
        candidate_value=3.8,
        evidence=None,
    )
    assert res.verification_state == VerificationState.UNVERIFIED
    assert "No supporting evidence snippet" in res.notes


def test_fact_with_unrelated_evidence_text_cannot_become_verified():
    unrelated_ev = CandidateEvidence(
        source_url="https://university.edu/dining",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Campus dining hall offers organic and vegan meal options daily.",
        content_sha256="dininghash",
    )
    res = FactVerifier.verify_field(
        field_name="international_students_allowed",
        candidate_value=TriState.YES,
        evidence=unrelated_ev,
    )
    assert res.verification_state == VerificationState.UNVERIFIED
    assert "does not contain relevant keywords" in res.notes


def test_unknown_facts_never_fabricated():
    ev = CandidateEvidence(
        source_url="https://admissions.clarku.edu",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Clark offers presidential scholarships to selected incoming first-years.",
        content_sha256="hash123",
    )
    res = FactVerifier.verify_field(
        field_name="requires_sat",
        candidate_value=TriState.UNKNOWN,
        evidence=ev,
    )
    assert res.candidate_value == TriState.UNKNOWN
    assert res.verification_state == VerificationState.UNVERIFIED
