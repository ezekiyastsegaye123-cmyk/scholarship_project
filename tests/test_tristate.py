"""Tests for TriState multi-state semantics.

Critical Rule:
- Missing information MUST NOT become FALSE.
- UNKNOWN != NO.
- UNKNOWN != False.
"""
import pytest
from pydantic import ValidationError

from scholarship_intelligence.domain.enums import TriState
from scholarship_intelligence.schemas.opportunity import ScholarshipOpportunityCreate


def test_tristate_enum_values():
    """Verifies all five explicit TriState values exist."""
    assert TriState.YES.value == "YES"
    assert TriState.NO.value == "NO"
    assert TriState.UNKNOWN.value == "UNKNOWN"
    assert TriState.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert TriState.CONFLICTING.value == "CONFLICTING"


def test_tristate_unknown_not_false_or_no():
    """Enforces strict invariant: UNKNOWN is neither NO nor False."""
    assert TriState.UNKNOWN != TriState.NO
    assert TriState.UNKNOWN.value != "NO"
    assert TriState.UNKNOWN != False  # noqa: E712
    assert (TriState.UNKNOWN == False) is False  # noqa: E712
    assert (TriState.UNKNOWN == True) is False  # noqa: E712
    
    # Truthiness of string enum: both YES and UNKNOWN evaluate as non-empty strings in Python,
    # but their semantic values are completely distinct.
    assert TriState.UNKNOWN != TriState.NOT_APPLICABLE
    assert TriState.UNKNOWN != TriState.CONFLICTING


def test_tristate_in_schema_defaults_to_unknown():
    """Verifies that schema fields default to UNKNOWN rather than False."""
    opp = ScholarshipOpportunityCreate(
        title="Test Award",
        slug="test-award",
    )
    assert opp.international_students_allowed == TriState.UNKNOWN
    assert opp.requires_sat == TriState.UNKNOWN
    assert opp.requires_act == TriState.UNKNOWN
    assert opp.requires_css_profile == TriState.UNKNOWN
    assert opp.financial_need_required == TriState.UNKNOWN


def test_tristate_invalid_value_rejection():
    """Verifies that arbitrary strings or raw booleans are not silently accepted."""
    with pytest.raises(ValidationError):
        ScholarshipOpportunityCreate(
            title="Test Award",
            slug="test-award",
            international_students_allowed="MAYBE",  # Invalid enum value
        )
