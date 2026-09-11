"""Boundary and scope tests for Phase 1B.

Explicitly verifies that Phase 1B does NOT evaluate eligibility,
does NOT verify truth, does NOT score trust, and does NOT calculate match scores.
"""
from pathlib import Path
import pytest

from scholarship_intelligence.domain.enums import TriState
from scholarship_intelligence.ingestion.runner import IngestionRunner
from scholarship_intelligence.schemas.candidate import CandidateOpportunity, CandidateStagingResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_phase_1b_does_not_evaluate_eligibility():
    """Verifies that Phase 1B only extracts candidate criteria and does not evaluate a student."""
    html = (FIXTURES_DIR / "normal_scholarship.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/scholarships/global-leaders")

    # 1. Output must be a CandidateStagingResult
    assert isinstance(result, CandidateStagingResult)
    assert isinstance(result.candidate, CandidateOpportunity)

    # 2. Assert candidate object contains NO student evaluation fields
    assert not hasattr(result.candidate, "is_eligible")
    assert not hasattr(result.candidate, "eligibility_status")
    assert not hasattr(result.candidate, "student_match")
    assert not hasattr(result.candidate, "evaluated_student_id")


def test_phase_1b_does_not_verify_truth_or_assign_trust_scores():
    """Verifies that Phase 1B does not assign verification truth or trust scores."""
    html = (FIXTURES_DIR / "table_scholarship.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/fellowship")

    assert result.candidate is not None
    assert not hasattr(result.candidate, "trust_score")
    assert not hasattr(result.candidate, "verification_score")
    assert not hasattr(result.candidate, "confidence_rating")
    assert not hasattr(result.candidate, "verification_state")

    # Extraction status is purely a technical marker, NOT a verification state
    assert result.candidate.extraction_status == "EXTRACTED"


def test_phase_1b_does_not_rank_or_recommend():
    """Verifies that Phase 1B does not rank, score, or provide recommendations."""
    html = (FIXTURES_DIR / "normal_scholarship.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(html, "https://example.edu/scholarships/global-leaders")

    assert not hasattr(result, "rank")
    assert not hasattr(result, "recommendation_reason")
    assert not hasattr(result, "match_score")
    assert not hasattr(result, "counselor_notes")
