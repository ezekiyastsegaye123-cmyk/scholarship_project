"""Tests for Phase 2 FastAPI backend endpoints."""
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from scholarship_intelligence.api.app import app
from scholarship_intelligence.db.session import get_db_session
from scholarship_intelligence.domain.enums import VerificationState
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity

client = TestClient(app)


@pytest.fixture
def existing_opportunity_id():
    """Fetches an existing opportunity ID from the seeded SQLite database."""
    with get_db_session() as session:
        opp = session.query(ScholarshipOpportunity).first()
        assert opp is not None, "Database must contain seeded opportunities"
        return str(opp.id)


def test_health_endpoint():
    """Verify application health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Phase 2" in data["phase"]


def test_list_opportunities_pagination():
    """Verify opportunity listing with default pagination."""
    response = client.get("/api/opportunities?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5
    assert data["total"] >= 18  # 18 seeded opportunities from Phase 1


def test_list_opportunities_search():
    """Verify search filter across opportunities."""
    response = client.get("/api/opportunities?search=Harvard")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Harvard" in item["title"] for item in data["items"])


def test_list_opportunities_filtering():
    """Verify filtering by verification_status and funding_type."""
    response = client.get("/api/opportunities?verification_status=VERIFIED")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["verification_status"] == "VERIFIED"


def test_get_opportunity_detail_success(existing_opportunity_id):
    """Verify detail retrieval for an existing opportunity."""
    response = client.get(f"/api/opportunities/{existing_opportunity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == existing_opportunity_id
    assert "title" in data
    assert "award_details" in data
    assert "deadlines" in data
    assert "eligibility_rules" in data
    assert "requirements" in data
    assert "official_sources" in data


def test_get_opportunity_detail_not_found():
    """Verify 404 on nonexistent opportunity ID."""
    response = client.get("/api/opportunities/nonexistent-id-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_student_profile_privacy_enforcement():
    """Verify privacy validator strictly rejects forbidden fields."""
    valid_payload = {
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "gpa": 3.85,
        "gpa_scale": 4.0,
        "intended_major": "Computer Science",
    }
    res_valid = client.post("/api/student-profile", json=valid_payload)
    assert res_valid.status_code == 200
    assert res_valid.json()["citizenship_country"] == "ETH"

    # Forbidden: SSN
    invalid_payload = {**valid_payload, "ssn": "000-12-3456"}
    res_invalid = client.post("/api/student-profile", json=invalid_payload)
    assert res_invalid.status_code == 422

    # Forbidden: bank_account
    invalid_bank = {**valid_payload, "bank_account": "1234567890"}
    res_bank = client.post("/api/student-profile", json=invalid_bank)
    assert res_bank.status_code == 422


def test_evaluate_opportunity_endpoint(existing_opportunity_id):
    """Verify deterministic eligibility evaluation endpoint."""
    payload = {
        "profile": {
            "citizenship_country": "ETH",
            "residence_country": "ETH",
            "gpa": 3.9,
            "gpa_scale": 4.0,
        },
        "target_academic_cycle": "2026-2027",
    }
    response = client.post(f"/api/opportunities/{existing_opportunity_id}/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "explanations" in data
    assert "is_gated" in data


def test_counsel_opportunity_endpoint(existing_opportunity_id):
    """Verify qualitative counselor assessment endpoint."""
    payload = {
        "profile": {
            "citizenship_country": "ETH",
            "residence_country": "ETH",
            "gpa": 3.9,
            "gpa_scale": 4.0,
            "prepared_materials": ["Official Transcript", "Recommendation Letter"],
        },
        "reference_date": "2026-11-01",
    }
    response = client.post(f"/api/opportunities/{existing_opportunity_id}/counsel", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "academic_alignment" in data
    assert "geographic_alignment" in data
    assert "application_readiness" in data
    assert "funding_assessment" in data
    assert "strengths" in data
    assert "gaps" in data
    assert "recommended_next_steps" in data


def test_compare_opportunities_endpoint(existing_opportunity_id):
    """Verify comparison endpoint across multiple opportunities."""
    # Fetch two opportunity IDs
    with get_db_session() as session:
        opps = session.query(ScholarshipOpportunity).limit(2).all()
        opp_ids = [str(o.id) for o in opps]

    payload = {
        "opportunity_ids": opp_ids,
        "profile": {
            "citizenship_country": "ETH",
            "residence_country": "ETH",
            "gpa": 3.85,
        },
        "reference_date": "2026-11-01",
    }
    response = client.post("/api/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total_compared"] == len(opp_ids)
    assert "ordering_rule" in data
    for item in data["items"]:
        assert "opportunity_title" in item
        assert "funding_classification" in item
        assert "academic_alignment" in item
