"""Tests for UNKNOWN semantics preservation in Phase 1C verification."""
import pytest
from scholarship_intelligence.domain.enums import AuthorityTier, TriState, VerificationState
from scholarship_intelligence.schemas.candidate import CandidateEvidence, CandidateOpportunity
from scholarship_intelligence.verification.conflict import ConflictEngine
from scholarship_intelligence.verification.fact_verifier import FactVerifier


def test_tristate_unknown_is_not_false_or_no_or_na():
    assert TriState.UNKNOWN != TriState.NO
    assert TriState.UNKNOWN != TriState.NOT_APPLICABLE
    assert TriState.UNKNOWN != TriState.CONFLICTING
    assert TriState.UNKNOWN.value == "UNKNOWN"


def test_unmentioned_facts_remain_unknown_in_verification():
    ev = CandidateEvidence(
        source_url="https://admissions.harvard.edu",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Harvard undergraduate admissions is need-blind for all students.",
        content_sha256="hash123",
    )

    # requires_sat was not mentioned on the page -> UNKNOWN
    res = FactVerifier.verify_field("requires_sat", TriState.UNKNOWN, ev)
    assert res.candidate_value == TriState.UNKNOWN
    # Stays UNVERIFIED / UNKNOWN without fabricating NO
    assert res.verification_state == VerificationState.UNVERIFIED
    assert "Preserved as UNKNOWN; no fact invented" in res.notes


def test_unknown_does_not_conflict_with_known_canonical_value():
    """If an ingested candidate page doesn't mention SAT requirement (UNKNOWN),
    it must NOT contradict an existing verified record stating requires_sat=YES."""
    is_conflict = ConflictEngine.detect_fact_discrepancy(
        field_name="requires_sat",
        val_a=TriState.UNKNOWN,
        val_b=TriState.YES,
    )
    assert is_conflict is False
