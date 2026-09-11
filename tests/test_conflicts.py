"""Tests for conflict logging and preservation of discrepant sources."""
from datetime import datetime
from scholarship_intelligence.domain.enums import ConflictStatus
from scholarship_intelligence.schemas.verification import ConflictRecordCreate


def test_conflict_preserves_both_sources_without_overwriting():
    """Verifies that discrepant values from different sources are explicitly logged."""
    conflict = ConflictRecordCreate(
        field_name="application_deadline",
        source_a_value="January 15, 2027",
        source_a_url="https://clarku.edu/admissions/deadlines",
        source_b_value="March 1, 2027",
        source_b_url="https://aggregatorsite.com/clark-deadlines",
        resolution_status=ConflictStatus.RESOLVED_OFFICIAL_PREFERRED,
        resolution_notes="Official university portal takes precedence over aggregator directory date.",
        recorded_at=datetime(2026, 9, 10, 12, 0, 0),
    )
    assert conflict.field_name == "application_deadline"
    assert conflict.source_a_value == "January 15, 2027"
    assert conflict.source_b_value == "March 1, 2027"
    assert conflict.resolution_status == ConflictStatus.RESOLVED_OFFICIAL_PREFERRED
    assert conflict.source_a_url != conflict.source_b_url
