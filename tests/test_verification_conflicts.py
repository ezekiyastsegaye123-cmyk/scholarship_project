"""Tests for Phase 1C conflict detection and deterministic resolution rules."""
import pytest
from scholarship_intelligence.domain.enums import AuthorityTier, ConflictStatus
from scholarship_intelligence.verification.conflict import ConflictEngine


def test_conflict_resolution_authority_tier_precedence():
    """Official university portal outranks third-party aggregator."""
    outcome = ConflictEngine.resolve_conflict(
        field_name="application_deadline",
        value_a="2027-02-01",
        source_a_url="https://admissions.clarku.edu/deadlines",
        source_a_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_a_evidence="Application deadline is February 1, 2027.",
        cycle_a="2026-2027",
        value_b="2027-03-15",
        source_b_url="https://fastweb.com/clark-deadline",
        source_b_tier=AuthorityTier.DISCOVERY_AGGREGATOR,
        source_b_evidence="Deadline listed as March 15.",
        cycle_b="2026-2027",
        current_cycle="2026-2027",
    )

    assert outcome.is_resolved is True
    assert outcome.winning_value == "2027-02-01"
    assert outcome.winning_tier == AuthorityTier.OFFICIAL_UNIVERSITY
    assert outcome.resolution_status == ConflictStatus.RESOLVED_OFFICIAL_PREFERRED
    assert "Official source" in outcome.rationale


def test_conflict_resolution_cycle_recency_precedence():
    """When authority is equal, current academic cycle outranks prior cycle."""
    outcome = ConflictEngine.resolve_conflict(
        field_name="award_amount",
        value_a="25000",
        source_a_url="https://university.edu/aid-2026",
        source_a_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_a_evidence="For 2026-2027, awards are 5,000.",
        cycle_a="2026-2027",
        value_b="20000",
        source_b_url="https://university.edu/aid-2024",
        source_b_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_b_evidence="For 2024-2025, awards are 0,000.",
        cycle_b="2024-2025",
        current_cycle="2026-2027",
    )

    assert outcome.is_resolved is True
    assert outcome.winning_value == "25000"
    assert outcome.resolution_status == ConflictStatus.RESOLVED_RECENCY_PREFERRED
    assert "current academic cycle" in outcome.rationale


def test_conflict_unresolved_between_two_official_sources():
    """Two official sources disagree for the same cycle -> OPEN conflict, no guessing."""
    outcome = ConflictEngine.resolve_conflict(
        field_name="priority_deadline",
        value_a="2026-12-01",
        source_a_url="https://admissions.university.edu/deadlines",
        source_a_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_a_evidence="Priority scholarship deadline is December 1, 2026.",
        cycle_a="2026-2027",
        value_b="2027-01-15",
        source_b_url="https://finaid.university.edu/scholarships",
        source_b_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_b_evidence="All scholarship applications must be received by January 15, 2027.",
        cycle_b="2026-2027",
        current_cycle="2026-2027",
    )

    assert outcome.is_resolved is False
    assert outcome.winning_value is None
    assert outcome.resolution_status == ConflictStatus.OPEN
    assert "Unresolvable conflict between sources of equal authority" in outcome.rationale
    assert outcome.conflict_record.source_a_value == "2026-12-01"
    assert outcome.conflict_record.source_b_value == "2027-01-15"
