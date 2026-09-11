"""Tests for counselor deadline evaluation, deterministic thresholds, and preservation of multiple deadlines."""
from datetime import date
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.enums import DeadlineReadiness
from scholarship_intelligence.counselor.rules import assess_deadlines
from scholarship_intelligence.domain.enums import DeadlineType


def test_deadline_closing_soon_and_open_thresholds():
    ref_date = date(2026, 11, 1)
    opp = MagicMock()

    # 1. Closing soon deadline (within 14 days, e.g. 10 days away)
    d_soon = MagicMock()
    d_soon.deadline_type = DeadlineType.SCHOLARSHIP_APPLICATION.value
    d_soon.deadline_date = date(2026, 11, 10)
    d_soon.is_exact_date = True
    d_soon.timezone = "America/New_York"
    d_soon.context_description = "Scholarship portal deadline"

    # 2. Open deadline (> 14 days away, e.g. 60 days away)
    d_open = MagicMock()
    d_open.deadline_type = DeadlineType.FINANCIAL_AID.value
    d_open.deadline_date = date(2027, 1, 1)
    d_open.is_exact_date = True
    d_open.timezone = "America/New_York"
    d_open.context_description = "ISFAA submission deadline"

    opp.deadlines = [d_soon, d_open]

    ctx = assess_deadlines(opp, reference_date=ref_date)
    assert len(ctx.deadlines) == 2
    assert ctx.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx.deadlines[0].days_remaining == 9
    assert ctx.deadlines[1].readiness == DeadlineReadiness.OPEN
    assert ctx.deadlines[1].days_remaining == 61
    assert ctx.has_passed_deadline is False
    assert ctx.earliest_upcoming_deadline.deadline_type == DeadlineType.SCHOLARSHIP_APPLICATION


def test_multiple_deadlines_preserved_independently():
    """Verify distinct deadline types (e.g. University application vs Financial aid) are not collapsed."""
    ref_date = date(2026, 10, 1)
    opp = MagicMock()

    d1 = MagicMock(deadline_type=DeadlineType.UNIVERSITY_APPLICATION.value, deadline_date=date(2026, 12, 1), is_exact_date=True)
    d2 = MagicMock(deadline_type=DeadlineType.FINANCIAL_AID.value, deadline_date=date(2027, 2, 1), is_exact_date=True)
    opp.deadlines = [d1, d2]

    ctx = assess_deadlines(opp, reference_date=ref_date)
    types_found = [d.deadline_type for d in ctx.deadlines]
    assert DeadlineType.UNIVERSITY_APPLICATION in types_found
    assert DeadlineType.FINANCIAL_AID in types_found
    assert len(ctx.deadlines) == 2


def test_passed_deadline_flags_has_passed():
    ref_date = date(2026, 11, 1)
    opp = MagicMock()

    d_past = MagicMock(deadline_type=DeadlineType.EARLY_DECISION.value, deadline_date=date(2026, 10, 15), is_exact_date=True)
    opp.deadlines = [d_past]

    ctx = assess_deadlines(opp, reference_date=ref_date)
    assert ctx.deadlines[0].readiness == DeadlineReadiness.CLOSED
    assert ctx.deadlines[0].days_remaining < 0
    assert ctx.has_passed_deadline is True
