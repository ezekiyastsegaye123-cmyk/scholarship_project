"""Automated tests for evidence preservation and deterministic content hashing."""
from pathlib import Path
from datetime import datetime, timezone
import pytest

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.runner import IngestionRunner
from scholarship_intelligence.schemas.candidate import CandidateEvidence

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_deterministic_content_hashing():
    """Verifies SHA-256 changes when content changes, and is identical for same content."""
    html_v1 = (FIXTURES_DIR / "changed_content_v1.html").read_bytes()
    html_v2 = (FIXTURES_DIR / "changed_content_v2.html").read_bytes()

    hash_v1_a = PoliteHttpClient.compute_sha256(html_v1)
    hash_v1_b = PoliteHttpClient.compute_sha256(html_v1)
    hash_v2 = PoliteHttpClient.compute_sha256(html_v2)

    assert hash_v1_a == hash_v1_b
    assert hash_v1_a != hash_v2


def test_evidence_traceability_on_candidate_facts():
    """Verifies all candidate facts retain complete source provenance and concise quotes."""
    html = (FIXTURES_DIR / "normal_scholarship.html").read_text(encoding="utf-8")
    runner = IngestionRunner()
    result = runner.ingest_html(
        html=html,
        source_url="https://example.edu/scholarships/global-leaders",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
    )

    assert result.candidate is not None
    candidate = result.candidate

    # Verify award evidence
    assert candidate.award is not None
    assert candidate.award.evidence.source_url == "https://example.edu/scholarships/global-leaders"
    assert candidate.award.evidence.http_status == 200
    assert candidate.award.evidence.authority_tier == AuthorityTier.OFFICIAL_UNIVERSITY
    assert len(candidate.award.evidence.evidence_text) <= 280
    assert "$25,000" in candidate.award.evidence.evidence_text

    # Verify deadline evidence
    assert len(candidate.deadlines) >= 1
    for dl in candidate.deadlines:
        assert dl.evidence.source_url == "https://example.edu/scholarships/global-leaders"
        assert dl.evidence.content_sha256 is not None
        assert len(dl.evidence.evidence_text) > 0

    # Verify requirements evidence
    assert len(candidate.requirements) >= 1
    for req in candidate.requirements:
        assert req.evidence.source_url == "https://example.edu/scholarships/global-leaders"
        assert len(req.evidence.evidence_text) <= 280


def test_candidate_evidence_immutability():
    """Verifies CandidateEvidence is frozen/immutable to prevent tampering."""
    ev = CandidateEvidence(
        source_url="https://example.edu/aid",
        retrieved_at=datetime.now(timezone.utc),
        http_status=200,
        content_sha256="abcdef1234567890",
        evidence_text="Full tuition covered",
    )
    with pytest.raises(Exception):
        ev.evidence_text = "Modified quote"
