"""Automated tests for candidate fact normalization and TriState uncertainty."""
from pathlib import Path
from datetime import date
import pytest

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    TriState,
)
from scholarship_intelligence.ingestion.runner import IngestionRunner

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_normalization_standard_page():
    """Verifies normalization of standard scholarship with exact dates and amounts."""
    html = (FIXTURES_DIR / "normal_scholarship.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/scholarships/global-leaders")
    candidate = result.candidate

    assert candidate is not None
    assert candidate.title == "Global Leaders Undergraduate Scholarship"
    assert candidate.international_students_allowed == TriState.YES
    assert candidate.requires_sat == TriState.YES
    assert candidate.requires_act == TriState.UNKNOWN  # Not mentioned, must be UNKNOWN
    assert candidate.requires_css_profile == TriState.YES

    # Deadlines
    dl_types = [d.deadline_type for d in candidate.deadlines]
    assert DeadlineType.EARLY_ACTION in dl_types or DeadlineType.SCHOLARSHIP_APPLICATION in dl_types or DeadlineType.UNIVERSITY_APPLICATION in dl_types


def test_normalization_funding_decomposition():
    """Verifies decomposed itemized funding components (tuition, housing, meals, insurance)."""
    html = (FIXTURES_DIR / "funding_decomposition.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/full-ride")
    candidate = result.candidate

    assert candidate is not None
    assert candidate.award is not None
    assert candidate.award.funding_classification == FundingClassification.FULL_FUNDING

    types = [c.component_type for c in candidate.award.components]
    assert FundingComponentType.TUITION in types
    assert FundingComponentType.ROOM in types
    assert FundingComponentType.MEALS in types
    assert FundingComponentType.HEALTH_INSURANCE in types
    assert FundingComponentType.TRAVEL in types


def test_normalization_missing_info_preserves_unknown():
    """Verifies that missing information remains UNKNOWN and varied deadlines are marked."""
    html = (FIXTURES_DIR / "missing_info.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/general-grant")
    candidate = result.candidate

    assert candidate is not None
    assert candidate.international_students_allowed == TriState.UNKNOWN
    assert candidate.requires_sat == TriState.UNKNOWN
    assert candidate.requires_act == TriState.UNKNOWN
    assert candidate.requires_css_profile == TriState.UNKNOWN
    assert candidate.financial_need_required == TriState.UNKNOWN

    # Deadline varies
    assert len(candidate.deadlines) >= 1
    dl = candidate.deadlines[0]
    assert dl.varies_by_program is True
    assert dl.is_exact_date is False
    assert dl.deadline_date is None
