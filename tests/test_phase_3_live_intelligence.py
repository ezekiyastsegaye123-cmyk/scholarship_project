"""Comprehensive verification suite for Phase 3 Live Scholarship Intelligence.

Tests cover:
1. SSRF Prevention & Redirect Security
2. Content Hashing & Change Detection
3. Source Registry & Idempotent Seeding
4. Deterministic Freshness Classification
5. End-to-End Live Ingestion Pipeline & Fact Updates
6. Audit Ledger & Verification History Endpoints
"""
from datetime import date, datetime, timedelta, timezone
import json
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scholarship_intelligence.api.app import app
from scholarship_intelligence.domain.enums import AuthorityTier, VerificationState
from scholarship_intelligence.ingestion.change_detector import ChangeDetector
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.freshness import FreshnessClassifier, FreshnessLevel
from scholarship_intelligence.ingestion.pipeline import IngestionPipeline
from scholarship_intelligence.ingestion.safety import IngestionSafetyError, validate_url
from scholarship_intelligence.ingestion.source_registry import SourceRegistry
from scholarship_intelligence.ingestion.status import FetchStatusCategory
from scholarship_intelligence.models.base import Base
from scholarship_intelligence.models.ingestion_run import IngestionRun
from scholarship_intelligence.models.ingestion_source import IngestionSource
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.source import OfficialSource
from scholarship_intelligence.models.verification import VerificationRecord
from scholarship_intelligence.models.verification_history import VerificationHistory
from fastapi.testclient import TestClient


@pytest.fixture
def db_session():
    """In-memory SQLite session with clean table creation."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ==============================================================================
# 1. SSRF Prevention & Redirect Security Tests
# ==============================================================================

def test_ssrf_blocks_private_and_cloud_metadata_ips():
    """Validates that RFC 1918, loopback, and cloud metadata IPs are strictly rejected."""
    blocked_targets = [
        "http://127.0.0.1/admin",
        "http://127.0.0.2:8080/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
        "http://172.16.0.1/",
        "http://192.168.1.1/secret",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://instance-data/latest/meta-data/",
        "http://localhost:8000/",
        "http://server.local/",
        "ftp://example.com/file",
        "file:///etc/passwd",
    ]

    for target in blocked_targets:
        with pytest.raises(IngestionSafetyError):
            validate_url(target, check_dns=False)


def test_client_blocks_ssrf_via_redirect():
    """Ensures polite client catches redirect attempts to private cloud metadata."""
    def mock_handler(request: httpx.Request):
        if str(request.url) == "http://public-scholarship.org/apply":
            # Redirect to AWS metadata IP
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})
        return httpx.Response(200, text="OK")

    transport = httpx.MockTransport(mock_handler)
    client = PoliteHttpClient(transport=transport, delay_between_requests=0.0)

    res = client.fetch("http://public-scholarship.org/apply")
    assert res.status_category == FetchStatusCategory.INVALID_CONTENT
    assert "SSRF blocked on redirect" in (res.error_message or "")
    assert len(res.redirect_chain) == 1
    assert res.redirect_chain[0] == "http://public-scholarship.org/apply"


def test_client_tracks_legitimate_redirect_chain():
    """Ensures polite client tracks legitimate redirects and completes successfully."""
    def mock_handler(request: httpx.Request):
        url_str = str(request.url)
        if url_str == "http://public-scholarship.org/old-path":
            return httpx.Response(301, headers={"Location": "http://public-scholarship.org/new-path"})
        elif url_str == "http://public-scholarship.org/new-path":
            return httpx.Response(200, text="<html><body><h1>Scholarship Active</h1></body></html>", headers={"Content-Type": "text/html"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    client = PoliteHttpClient(transport=transport, delay_between_requests=0.0)

    res = client.fetch("http://public-scholarship.org/old-path")
    assert res.status_category == FetchStatusCategory.SUCCESS
    assert res.http_status == 200
    assert len(res.redirect_chain) == 1
    assert res.redirect_chain[0] == "http://public-scholarship.org/old-path"
    assert res.retrieval_duration_seconds >= 0.0


# ==============================================================================
# 2. Content Hashing & Granular Fact Change Detection Tests
# ==============================================================================

def test_content_hashing_and_change_detection():
    """Validates SHA-256 hash detection between identical and modified responses."""
    content_v1 = "<html><body><h1>Merit Scholarship</h1><p>Award: $10,000</p></body></html>"
    content_v2 = "<html><body><h1>Merit Scholarship</h1><p>Award: $15,000</p></body></html>"

    sha_v1 = PoliteHttpClient.compute_sha256(content_v1.encode("utf-8"))
    sha_v1_dup = PoliteHttpClient.compute_sha256(content_v1.encode("utf-8"))
    sha_v2 = PoliteHttpClient.compute_sha256(content_v2.encode("utf-8"))

    assert sha_v1 == sha_v1_dup
    assert sha_v1 != sha_v2

    comp_unchanged = ChangeDetector.compare_content_hashes(sha_v1, sha_v1_dup)
    assert not comp_unchanged.content_changed

    comp_changed = ChangeDetector.compare_content_hashes(sha_v1, sha_v2)
    assert comp_changed.content_changed


# ==============================================================================
# 3. Source Registry & Idempotency Tests
# ==============================================================================

def test_source_registry_seeding_is_idempotent(db_session):
    """Verifies that seeding sources multiple times does not create duplicates."""
    first_seed = SourceRegistry.seed_default_sources(db_session)
    assert len(first_seed) >= 4

    total_first = db_session.query(IngestionSource).count()
    assert total_first == len(first_seed)

    # Second seed
    second_seed = SourceRegistry.seed_default_sources(db_session)
    assert len(second_seed) == 0

    total_second = db_session.query(IngestionSource).count()
    assert total_second == total_first


def test_source_registry_due_only_filtering(db_session):
    """Verifies that due_only filters sources correctly based on crawl interval."""
    ref_time = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    
    # Source A: never crawled -> due
    s_a = SourceRegistry.register_source(
        db_session, name="Source A", url="https://university-a.edu/aid", fetch_interval_hours=24
    )
    # Source B: crawled 2 hours ago (interval 24h) -> not due
    s_b = SourceRegistry.register_source(
        db_session, name="Source B", url="https://university-b.edu/aid", fetch_interval_hours=24
    )
    SourceRegistry.record_crawl_result(
        db_session, s_b.id, http_status=200, content_sha256="abc",
        crawled_at=ref_time - timedelta(hours=2), success=True
    )
    # Source C: crawled 48 hours ago (interval 24h) -> due
    s_c = SourceRegistry.register_source(
        db_session, name="Source C", url="https://university-c.edu/aid", fetch_interval_hours=24
    )
    SourceRegistry.record_crawl_result(
        db_session, s_c.id, http_status=200, content_sha256="xyz",
        crawled_at=ref_time - timedelta(hours=48), success=True
    )

    due_sources = SourceRegistry.get_active_sources(db_session, due_only=True, reference_time=ref_time)
    due_urls = {s.url for s in due_sources}

    assert "https://university-a.edu/aid" in due_urls
    assert "https://university-c.edu/aid" in due_urls
    assert "https://university-b.edu/aid" not in due_urls


# ==============================================================================
# 4. Deterministic Freshness Classification Tests
# ==============================================================================

def test_freshness_classifier_thresholds(db_session):
    """Verifies FRESH (<=30d), MODERATE (31-90d), STALE (>90d), and UNVERIFIED levels."""
    ref_time = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    # 1. Unverified opportunity
    opp_unverified = ScholarshipOpportunity(
        title="Unverified Opportunity",
        slug="unverified-opp",
        verification_status=VerificationState.UNVERIFIED.value,
        fingerprint_sha256="fp1",
    )
    db_session.add(opp_unverified)
    db_session.commit()

    f_unverif = FreshnessClassifier.classify(opp_unverified, reference_time=ref_time)
    assert f_unverif.level == FreshnessLevel.UNVERIFIED
    assert f_unverif.is_stale is True

    # 2. Fresh opportunity (verified 10 days ago)
    opp_fresh = ScholarshipOpportunity(
        title="Fresh Opportunity",
        slug="fresh-opp",
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="fp2",
    )
    db_session.add(opp_fresh)
    db_session.flush()
    db_session.add(
        VerificationRecord(
            scholarship_id=opp_fresh.id,
            verification_state="VERIFIED",
            verifier_identity="Verifier",
            verification_method="METHOD",
            evidence_url="https://example.edu",
            evidence_quote="Quote",
            verified_at=ref_time - timedelta(days=10),
        )
    )
    db_session.commit()

    f_fresh = FreshnessClassifier.classify(opp_fresh, reference_time=ref_time)
    assert f_fresh.level == FreshnessLevel.FRESH
    assert f_fresh.days_since_verification == 10
    assert f_fresh.is_stale is False

    # 3. Moderate opportunity (verified 45 days ago)
    opp_mod = ScholarshipOpportunity(
        title="Moderate Opportunity",
        slug="mod-opp",
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="fp3",
    )
    db_session.add(opp_mod)
    db_session.flush()
    db_session.add(
        VerificationRecord(
            scholarship_id=opp_mod.id,
            verification_state="VERIFIED",
            verifier_identity="Verifier",
            verification_method="METHOD",
            evidence_url="https://example.edu",
            evidence_quote="Quote",
            verified_at=ref_time - timedelta(days=45),
        )
    )
    db_session.commit()

    f_mod = FreshnessClassifier.classify(opp_mod, reference_time=ref_time)
    assert f_mod.level == FreshnessLevel.MODERATE
    assert f_mod.days_since_verification == 45
    assert f_mod.is_stale is False

    # 4. Stale opportunity (verified 120 days ago)
    opp_stale = ScholarshipOpportunity(
        title="Stale Opportunity",
        slug="stale-opp",
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="fp4",
    )
    db_session.add(opp_stale)
    db_session.flush()
    db_session.add(
        VerificationRecord(
            scholarship_id=opp_stale.id,
            verification_state="VERIFIED",
            verifier_identity="Verifier",
            verification_method="METHOD",
            evidence_url="https://example.edu",
            evidence_quote="Quote",
            verified_at=ref_time - timedelta(days=120),
        )
    )
    db_session.commit()

    f_stale = FreshnessClassifier.classify(opp_stale, reference_time=ref_time)
    assert f_stale.level == FreshnessLevel.STALE
    assert f_stale.days_since_verification == 120
    assert f_stale.is_stale is True


# ==============================================================================
# 5. End-to-End Live Ingestion Pipeline & Fact Change Tests
# ==============================================================================

def test_pipeline_end_to_end_and_fact_change_audit_ledger(db_session):
    """Full live pipeline lifecycle test:
    - Step 1: Initial crawl creates canonical record and initial history.
    - Step 2: Second crawl with identical content detects no content change and preserves facts.
    - Step 3: Third crawl with updated eligibility changes canonical fact and logs VerificationHistory.
    """
    url = "https://college.harvard.edu/aid/global"
    source = SourceRegistry.register_source(
        db_session,
        name="Harvard Global Aid",
        url=url,
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        fetch_interval_hours=24,
    )

    html_v1 = """
    <html>
      <head><title>Harvard International Financial Aid</title></head>
      <body>
        <h1>Harvard International Financial Aid</h1>
        <p>Eligibility: International students are eligible for all undergraduate financial aid.</p>
        <p>Testing: SAT is not required for 2026-2027 admissions.</p>
        <p>Deadline: Application deadline is January 1, 2027.</p>
        <p>Award: 100% full tuition coverage for all admitted students.</p>
      </body>
    </html>
    """

    html_v2_fact_change = """
    <html>
      <head><title>Harvard International Financial Aid</title></head>
      <body>
        <h1>Harvard International Financial Aid</h1>
        <p>Eligibility: International students are eligible for all undergraduate financial aid.</p>
        <p>Testing: SAT is required for all applicants starting 2026-2027 cycle.</p>
        <p>Deadline: Application deadline is January 1, 2027.</p>
        <p>Award: 100% full tuition coverage for all admitted students.</p>
      </body>
    </html>
    """

    current_html = html_v1

    def mock_handler(request: httpx.Request):
        if str(request.url) == url:
            return httpx.Response(200, text=current_html, headers={"Content-Type": "text/html"})
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    http_client = PoliteHttpClient(transport=mock_transport, delay_between_requests=0.0)

    from scholarship_intelligence.ingestion.runner import IngestionRunner
    from scholarship_intelligence.ingestion.extractor import HtmlExtractor
    from scholarship_intelligence.ingestion.normalizer import CandidateNormalizer

    runner = IngestionRunner(http_client=http_client, extractor=HtmlExtractor(), normalizer=CandidateNormalizer())
    pipeline = IngestionPipeline(runner=runner)

    # --- RUN 1: Initial Crawl ---
    t1 = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    summary_1 = pipeline.run(db_session, sources=[source], reference_time=t1)

    assert summary_1.status == "COMPLETED"
    assert summary_1.sources_succeeded == 1
    assert summary_1.opportunities_created == 1

    opp = db_session.query(ScholarshipOpportunity).first()
    assert opp is not None
    assert opp.title == "Harvard International Financial Aid"
    assert opp.requires_sat == "NO"

    # Verify initial history record exists
    histories_run1 = db_session.query(VerificationHistory).filter(VerificationHistory.scholarship_id == opp.id).all()
    assert len(histories_run1) >= 1
    assert histories_run1[0].decision == "PROMOTED_NEW_CANONICAL"

    # --- RUN 2: Idempotent Crawl with Identical Content ---
    t2 = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    summary_2 = pipeline.run(db_session, sources=[source], reference_time=t2)

    assert summary_2.status == "COMPLETED"
    assert summary_2.sources_succeeded == 1
    assert summary_2.opportunities_created == 0
    assert summary_2.opportunities_updated == 0

    # Verification history count unchanged
    histories_run2 = db_session.query(VerificationHistory).filter(VerificationHistory.scholarship_id == opp.id).all()
    assert len(histories_run2) == len(histories_run1)

    # --- RUN 3: Crawl with Updated Fact (requires_sat NO -> YES) ---
    current_html = html_v2_fact_change
    t3 = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
    summary_3 = pipeline.run(db_session, sources=[source], reference_time=t3)

    assert summary_3.status == "COMPLETED"
    assert summary_3.sources_succeeded == 1
    assert summary_3.opportunities_updated == 1

    db_session.refresh(opp)
    assert opp.requires_sat == "YES"

    # Verify fact modification history is logged with old and new values
    histories_run3 = db_session.query(VerificationHistory).filter(VerificationHistory.scholarship_id == opp.id).all()
    sat_history = next((h for h in histories_run3 if h.field_name == "requires_sat"), None)
    assert sat_history is not None
    assert sat_history.old_value == "NO"
    assert sat_history.new_value == "YES"
    assert sat_history.decision == "CANONICAL_UPDATE_VERIFIED"
    assert sat_history.new_evidence_quote is not None


# ==============================================================================
# 6. API Endpoints for Ingestion Runs, Sources, and Verification History
# ==============================================================================

def test_api_ingestion_and_verification_history_endpoints():
    """Verifies FastAPI routes for verification history and ingestion monitoring."""
    client = TestClient(app)

    # 1. Test Ingestion Runs endpoint
    runs_res = client.get("/api/ingestion/runs")
    assert runs_res.status_code == 200
    assert isinstance(runs_res.json(), list)

    # 2. Test Ingestion Sources endpoint
    sources_res = client.get("/api/ingestion/sources")
    assert sources_res.status_code == 200
    assert isinstance(sources_res.json(), list)

    # 3. Test Opportunities list contains freshness fields
    opps_res = client.get("/api/opportunities?page=1&page_size=5")
    assert opps_res.status_code == 200
    data = opps_res.json()
    assert "items" in data
    if data["items"]:
        first = data["items"][0]
        assert "freshness_level" in first
        assert first["freshness_level"] in ("FRESH", "MODERATE", "STALE", "UNVERIFIED")

        # 4. Test Verification History endpoint for opportunity
        opp_id = first["id"]
        hist_res = client.get(f"/api/opportunities/{opp_id}/verification-history")
        assert hist_res.status_code == 200
        assert isinstance(hist_res.json(), list)
