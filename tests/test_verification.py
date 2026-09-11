"""Tests for verification models and evidence states.

Enforces:
- No arbitrary numerical trust scores.
- QUARANTINED_FOR_REVIEW explicitly defined and verified.
- All 7 verification states active and distinct.
"""
from datetime import datetime
from scholarship_intelligence.domain.enums import VerificationState
from scholarship_intelligence.schemas.verification import VerificationRecordCreate


def test_verification_states():
    """Validates all 7 categorical verification states."""
    expected = {
        "VERIFIED",
        "PARTIALLY_VERIFIED",
        "CONFLICTING",
        "OUTDATED",
        "UNVERIFIED",
        "SOURCE_UNAVAILABLE",
        "QUARANTINED_FOR_REVIEW",
    }
    actual = {s.value for s in VerificationState}
    assert actual == expected


def test_quarantined_for_review_semantics():
    """Verifies QUARANTINED_FOR_REVIEW record creation for suspicious or risky listings."""
    rec = VerificationRecordCreate(
        verification_state=VerificationState.QUARANTINED_FOR_REVIEW,
        verifier_identity="Automated Risk Triage Rule",
        verification_method="CONTEXTUAL_FEE_ANALYSIS",
        evidence_url="https://example-external-portal.com/apply",
        evidence_quote="Send $50 via Western Union to guarantee award disbursement.",
        notes="Flagged for wire transfer disbursement scam. Quarantined for staff review.",
        verified_at=datetime(2026, 9, 10, 15, 0, 0),
    )
    assert rec.verification_state == VerificationState.QUARANTINED_FOR_REVIEW
    assert "disbursement scam" in rec.notes


def test_verified_record_with_official_citation():
    """Verifies standard VERIFIED state with verbatim institutional quote."""
    rec = VerificationRecordCreate(
        verification_state=VerificationState.VERIFIED,
        verifier_identity="Lead Scholarship Auditor",
        verification_method="PRIMARY_SOURCE_WEB_AUDIT",
        evidence_url="https://college.harvard.edu/financial-aid/types-aid/international-students",
        evidence_quote="Our financial aid program is completely need-blind to all applicants, domestic and international.",
        notes="Confirmed need-blind admissions for international applicants.",
        verified_at=datetime(2026, 9, 10, 16, 0, 0),
    )
    assert rec.verification_state == VerificationState.VERIFIED
    assert len(rec.evidence_quote) > 10
