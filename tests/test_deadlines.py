"""Tests for multi-deadline models and cycle semantics."""
from datetime import date
from scholarship_intelligence.domain.enums import DeadlineType
from scholarship_intelligence.schemas.deadline import DeadlineCreate


def test_multiple_deadlines_support():
    """Verifies that distinct deadline categories can be created and preserved."""
    d1 = DeadlineCreate(
        deadline_type=DeadlineType.EARLY_ACTION,
        deadline_date=date(2026, 11, 15),
        is_exact_date=True,
        academic_cycle="2026-2027",
        context_description="Early Action admission deadline",
    )
    d2 = DeadlineCreate(
        deadline_type=DeadlineType.PRIORITY,
        deadline_date=date(2026, 12, 1),
        is_exact_date=True,
        academic_cycle="2026-2027",
        context_description="Scholarship consideration priority cutoff",
    )
    d3 = DeadlineCreate(
        deadline_type=DeadlineType.REGULAR_DECISION,
        deadline_date=date(2027, 1, 15),
        is_exact_date=True,
        academic_cycle="2026-2027",
        context_description="Regular Decision final cutoff",
    )

    assert d1.deadline_type == DeadlineType.EARLY_ACTION
    assert d2.deadline_type == DeadlineType.PRIORITY
    assert d3.deadline_type == DeadlineType.REGULAR_DECISION
    assert d1.academic_cycle == "2026-2027"


def test_deadline_varies_by_program_and_unknown_dates():
    """Supports opportunities with rolling, variable, or unconfirmed deadlines."""
    d = DeadlineCreate(
        deadline_type=DeadlineType.ROLLING,
        deadline_date=None,
        is_exact_date=False,
        varies_by_program=True,
        context_description="Deadlines vary by department; review continues until cohorts fill.",
        source_evidence_snippet="Deadlines vary by academic program. Contact the department.",
    )
    assert d.deadline_date is None
    assert d.is_exact_date is False
    assert d.varies_by_program is True
    assert d.deadline_type == DeadlineType.ROLLING
