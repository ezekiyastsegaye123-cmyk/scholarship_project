"""Tests for multiple deadlines verification, cycle alignment, and differentiation."""
from datetime import date
import pytest

from scholarship_intelligence.domain.enums import AuthorityTier, DeadlineType, VerificationState
from scholarship_intelligence.schemas.candidate import CandidateDeadline, CandidateEvidence
from scholarship_intelligence.verification.fact_verifier import FactVerifier


def test_distinct_deadline_types_verified_independently():
    ev_app = CandidateEvidence(
        source_url="https://admissions.emory.edu",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="University application deadline is January 1, 2027.",
        content_sha256="hash1",
    )
    ev_schol = CandidateEvidence(
        source_url="https://admissions.emory.edu",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Emory Woodruff Scholars nomination deadline is November 15, 2026.",
        content_sha256="hash2",
    )

    deadlines = [
        CandidateDeadline(
            deadline_type=DeadlineType.UNIVERSITY_APPLICATION,
            raw_date_text="January 1, 2027",
            deadline_date=date(2027, 1, 1),
            is_exact_date=True,
            evidence=ev_app,
        ),
        CandidateDeadline(
            deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
            raw_date_text="November 15, 2026",
            deadline_date=date(2026, 11, 15),
            is_exact_date=True,
            evidence=ev_schol,
        ),
    ]

    results = FactVerifier.verify_deadlines(deadlines)
    assert len(results) == 2
    res_app = next(r for r in results if r.field_name == "deadline_UNIVERSITY_APPLICATION")
    res_schol = next(r for r in results if r.field_name == "deadline_SCHOLARSHIP_APPLICATION")

    assert res_app.verification_state == VerificationState.VERIFIED
    assert res_schol.verification_state == VerificationState.VERIFIED
    assert res_app.candidate_value != res_schol.candidate_value


def test_old_cycle_deadline_marked_outdated():
    ev_old = CandidateEvidence(
        source_url="https://admissions.emory.edu/archive",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="For the 2023-2024 academic year, deadline was November 15, 2023.",
        content_sha256="hashold",
    )
    dl = CandidateDeadline(
        deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
        raw_date_text="November 15, 2023",
        deadline_date=date(2023, 11, 15),
        is_exact_date=True,
        academic_cycle="2023-2024",
        evidence=ev_old,
    )

    results = FactVerifier.verify_deadlines([dl], target_cycle="2026-2027")
    assert len(results) == 1
    assert results[0].verification_state == VerificationState.OUTDATED
