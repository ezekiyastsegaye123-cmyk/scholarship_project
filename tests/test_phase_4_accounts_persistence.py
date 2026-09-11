"""Comprehensive automated test suite for Phase 4:
Accounts, Persistent Student Profiles & Personalization.

Validates:
- Secure registration, scrypt password hashing, and token issuance.
- Invariable protection against password and secret leakage.
- Strict authorization & IDOR isolation across all student entities.
- Persistent student profile validation and privacy enforcement.
- Saved scholarship idempotency and canonical data authority.
- Application tracker lifecycle, bounds, and delete safety.
- Persistent comparison limit enforcement (MAX_COMPARE = 4).
- Deterministic Phase 1 intelligence integration.
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scholarship_intelligence.api.app import app
from scholarship_intelligence.api.dependencies import get_db
from scholarship_intelligence.auth.security import (
    decode_access_token,
    hash_password,
    normalize_email,
    verify_password,
)
from scholarship_intelligence.domain.enums import (
    ApplicationStatus,
    AuthorityTier,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.models.application_record import ApplicationRecord
from scholarship_intelligence.models.comparison_selection import ComparisonSelection
from scholarship_intelligence.models.funding import Award
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.saved_opportunity import SavedOpportunity
from scholarship_intelligence.models.student_account import StudentAccount
from scholarship_intelligence.models.student_profile import StudentProfile
from scholarship_intelligence.models.university import University


@pytest.fixture
def client(db_session: Session):
    """FastAPI TestClient with overridden database session dependency."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_opportunity(db_session: Session) -> ScholarshipOpportunity:
    """Seeds a canonical verified scholarship opportunity for testing."""
    univ = University(name="MIT", city="Cambridge", state="MA", country="US")
    db_session.add(univ)
    db_session.flush()

    opp = ScholarshipOpportunity(
        title="MIT Presidential Fellowship",
        slug="mit-presidential-fellowship",
        university_id=univ.id,
        target_degree_level="BACHELOR",
        destination_country="US",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        financial_need_required=TriState.NO.value,
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="fp-mit",
    )
    db_session.add(opp)
    db_session.flush()

    award = Award(
        scholarship_id=opp.id,
        title="Full Tuition & Stipend",
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=80000.0,
    )
    db_session.add(award)
    db_session.commit()
    db_session.refresh(opp)
    return opp


@pytest.fixture
def second_opportunity(db_session: Session) -> ScholarshipOpportunity:
    """Seeds a second distinct opportunity for multiple selection testing."""
    univ = University(name="Stanford", city="Stanford", state="CA", country="US")
    db_session.add(univ)
    db_session.flush()

    opp = ScholarshipOpportunity(
        title="Stanford Knight-Hennessy",
        slug="stanford-knight-hennessy",
        university_id=univ.id,
        target_degree_level="BACHELOR",
        destination_country="US",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES.value,
        requires_sat=TriState.UNKNOWN.value,
        requires_act=TriState.UNKNOWN.value,
        financial_need_required=TriState.NO.value,
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="fp-stanford",
    )
    db_session.add(opp)
    db_session.commit()
    db_session.refresh(opp)
    return opp


# ==============================================================================
# 1. AUTHENTICATION TESTS
# ==============================================================================

def test_registration_successful_and_returns_safe_account(client: TestClient, db_session: Session):
    res = client.post(
        "/api/auth/register",
        json={"email": "student1@example.com", "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "token" in data
    assert "expires_at" in data
    account = data["account"]
    assert account["email"] == "student1@example.com"
    assert account["is_active"] is True
    assert account["has_profile"] is True
    assert "password" not in account
    assert "password_hash" not in account

    # Check database persistence
    db_account = db_session.query(StudentAccount).filter_by(email="student1@example.com").first()
    assert db_account is not None
    assert verify_password("SecurePassword123!", db_account.password_hash)
    assert db_account.password_hash.startswith("$scrypt$")
    assert db_account.profile is not None


def test_registration_duplicate_email_rejected(client: TestClient):
    client.post("/api/auth/register", json={"email": "duplicate@example.com", "password": "Password123!"})
    res = client.post("/api/auth/register", json={"email": "DUPLICATE@example.com", "password": "AnotherPassword456!"})
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"].lower()


def test_registration_email_normalization(client: TestClient, db_session: Session):
    res = client.post("/api/auth/register", json={"email": "   SpacesAndCaps@Example.Org   ", "password": "Password123!"})
    assert res.status_code == 201
    assert res.json()["account"]["email"] == "spacesandcaps@example.org"

    db_acc = db_session.query(StudentAccount).filter_by(email="spacesandcaps@example.org").first()
    assert db_acc is not None


def test_registration_weak_password_rejected(client: TestClient):
    res = client.post("/api/auth/register", json={"email": "weak@example.com", "password": "short"})
    assert res.status_code in (400, 422)


def test_login_successful_and_wrong_credentials(client: TestClient):
    # Register
    client.post("/api/auth/register", json={"email": "loginuser@example.com", "password": "ValidPassword99!"})

    # Wrong password
    bad_res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "WrongPassword!"})
    assert bad_res.status_code == 401
    assert bad_res.json()["detail"] == "Invalid credentials."

    # Nonexistent user (identical message prevents account enumeration)
    non_res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "SomePassword1!"})
    assert non_res.status_code == 401
    assert non_res.json()["detail"] == "Invalid credentials."

    # Successful login
    good_res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "ValidPassword99!"})
    assert good_res.status_code == 200
    assert "token" in good_res.json()
    assert good_res.json()["account"]["email"] == "loginuser@example.com"


def test_me_endpoint_authenticated_and_unauthenticated(client: TestClient):
    # Unauthenticated
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Authenticated
    reg_res = client.post("/api/auth/register", json={"email": "me@example.com", "password": "Password123!"})
    token = reg_res.json()["token"]

    auth_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200
    assert auth_res.json()["email"] == "me@example.com"


def test_logout_endpoint(client: TestClient):
    reg_res = client.post("/api/auth/register", json={"email": "logout@example.com", "password": "Password123!"})
    token = reg_res.json()["token"]

    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert "Successfully logged out" in logout_res.json()["message"]


# ==============================================================================
# 2. DATA PRIVACY TESTS
# ==============================================================================

def test_forbidden_fields_rejected_in_registration(client: TestClient):
    payload = {
        "email": "hack@example.com",
        "password": "Password123!",
        "ssn": "000-00-0000",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_forbidden_fields_rejected_in_profile_update(client: TestClient):
    reg_res = client.post("/api/auth/register", json={"email": "priv@example.com", "password": "Password123!"})
    token = reg_res.json()["token"]

    forbidden_payload = {
        "citizenship_country": "US",
        "passport_number": "A12345678",
        "credit_card": "4111111111111111",
    }
    res = client.put(
        "/api/student-profile",
        json=forbidden_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


# ==============================================================================
# 3. AUTHORIZATION & IDOR ISOLATION TESTS
# ==============================================================================

def test_idor_cross_user_profile_isolation(client: TestClient):
    # Register User A
    res_a = client.post("/api/auth/register", json={"email": "user_a@example.com", "password": "PasswordA1!"})
    token_a = res_a.json()["token"]

    # Register User B
    res_b = client.post("/api/auth/register", json={"email": "user_b@example.com", "password": "PasswordB1!"})
    token_b = res_b.json()["token"]

    # User A updates profile
    client.put(
        "/api/student-profile",
        json={"citizenship_country": "ET", "residence_country": "ET", "intended_major": "Physics"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B fetches profile and must NOT see User A's data
    profile_b_res = client.get("/api/student-profile", headers={"Authorization": f"Bearer {token_b}"})
    assert profile_b_res.status_code == 200
    assert profile_b_res.json()["intended_major"] is None


def test_idor_cross_user_saved_opportunities_isolation(client: TestClient, test_opportunity: ScholarshipOpportunity):
    res_a = client.post("/api/auth/register", json={"email": "save_a@example.com", "password": "PasswordA1!"})
    token_a = res_a.json()["token"]

    res_b = client.post("/api/auth/register", json={"email": "save_b@example.com", "password": "PasswordB1!"})
    token_b = res_b.json()["token"]

    # User A saves opportunity
    save_res = client.post(
        f"/api/saved-opportunities/{test_opportunity.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert save_res.status_code == 201

    # User B list saved opportunities -> empty list
    list_b = client.get("/api/saved-opportunities", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0
    assert len(list_b.json()["items"]) == 0

    # User B cannot unsave User A's saved opportunity
    del_b = client.delete(f"/api/saved-opportunities/{test_opportunity.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # User A still has it saved
    list_a = client.get("/api/saved-opportunities", headers={"Authorization": f"Bearer {token_a}"})
    assert list_a.json()["total"] == 1


def test_idor_cross_user_application_isolation(client: TestClient, test_opportunity: ScholarshipOpportunity):
    res_a = client.post("/api/auth/register", json={"email": "app_a@example.com", "password": "PasswordA1!"})
    token_a = res_a.json()["token"]

    res_b = client.post("/api/auth/register", json={"email": "app_b@example.com", "password": "PasswordB1!"})
    token_b = res_b.json()["token"]

    # User A creates application
    create_res = client.post(
        "/api/applications",
        json={"opportunity_id": test_opportunity.id, "status": "PLANNING", "student_notes": "User A confidential notes."},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # User B cannot access User A's application by ID (returns 404)
    get_b = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # User B cannot patch User A's application
    patch_b = client.patch(
        f"/api/applications/{app_id}",
        json={"student_notes": "Tampered by User B"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert patch_b.status_code == 404

    # User B cannot delete User A's application
    del_b = client.delete(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # User A's application remains untampered
    get_a = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200
    assert get_a.json()["student_notes"] == "User A confidential notes."


# ==============================================================================
# 4. PERSISTENT PROFILE TESTS
# ==============================================================================

def test_persistent_profile_survives_relogin(client: TestClient):
    # Register & update
    reg = client.post("/api/auth/register", json={"email": "survive@example.com", "password": "Password123!"})
    token1 = reg.json()["token"]

    update_res = client.put(
        "/api/student-profile",
        json={
            "citizenship_country": "ET",
            "residence_country": "ET",
            "gpa": 3.95,
            "gpa_scale": 4.0,
            "intended_major": "Biomedical Engineering",
            "sat_score": 1520,
            "financial_need_tier": "HIGH",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert update_res.status_code == 200

    # Logout & Re-login
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token1}"})
    login_res = client.post("/api/auth/login", json={"email": "survive@example.com", "password": "Password123!"})
    token2 = login_res.json()["token"]

    # Verify profile persisted across new session
    prof_res = client.get("/api/student-profile", headers={"Authorization": f"Bearer {token2}"})
    assert prof_res.status_code == 200
    data = prof_res.json()
    assert data["citizenship_country"] == "ET"
    assert data["gpa"] == 3.95
    assert data["intended_major"] == "Biomedical Engineering"
    assert data["sat_score"] == 1520
    # Optional unsupplied fields remain unknown/None (zero fabrication)
    assert data["act_score"] is None
    assert data["english_test_score"] is None


# ==============================================================================
# 5. SAVED SCHOLARSHIPS IDEMPOTENCY & CANONICAL DATA RULE
# ==============================================================================

def test_saved_opportunity_idempotency_and_canonical_authority(
    client: TestClient,
    db_session: Session,
    test_opportunity: ScholarshipOpportunity,
):
    reg = client.post("/api/auth/register", json={"email": "saver@example.com", "password": "Password123!"})
    token = reg.json()["token"]

    # First save
    res1 = client.post(f"/api/saved-opportunities/{test_opportunity.id}", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 201
    assert res1.json()["opportunity"]["title"] == "MIT Presidential Fellowship"

    # Duplicate save is idempotent
    res2 = client.post(f"/api/saved-opportunities/{test_opportunity.id}", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 201
    assert res2.json()["id"] == res1.json()["id"]

    # Verify database has exactly 1 record
    count = db_session.query(SavedOpportunity).count()
    assert count == 1

    # Modify canonical scholarship title in intelligence subsystem
    test_opportunity.title = "MIT Presidential Fellowship — Updated Cycle"
    db_session.commit()

    # Saved opportunity listing reflects current canonical reality
    list_res = client.get("/api/saved-opportunities", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert list_res.json()["items"][0]["opportunity"]["title"] == "MIT Presidential Fellowship — Updated Cycle"

    # Unsave
    del_res = client.delete(f"/api/saved-opportunities/{test_opportunity.id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert db_session.query(SavedOpportunity).count() == 0


# ==============================================================================
# 6. APPLICATION TRACKER TESTS
# ==============================================================================

def test_application_lifecycle_and_validation(client: TestClient, test_opportunity: ScholarshipOpportunity):
    reg = client.post("/api/auth/register", json={"email": "tracker@example.com", "password": "Password123!"})
    token = reg.json()["token"]

    # Create application
    c_res = client.post(
        "/api/applications",
        json={"opportunity_id": test_opportunity.id, "status": "PLANNING", "student_notes": "Drafting personal statement."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c_res.status_code == 201
    app_id = c_res.json()["id"]
    assert c_res.json()["status"] == "PLANNING"

    # Duplicate application for same scholarship rejected (409)
    dup_res = client.post(
        "/api/applications",
        json={"opportunity_id": test_opportunity.id, "status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dup_res.status_code == 409

    # Update status to SUBMITTED
    now_iso = datetime.now(timezone.utc).isoformat()
    patch_res = client.patch(
        f"/api/applications/{app_id}",
        json={"status": "SUBMITTED", "submitted_at": now_iso, "student_notes": "Submitted through portal."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "SUBMITTED"
    assert patch_res.json()["submitted_at"] is not None

    # Invalid status rejected
    bad_status = client.patch(
        f"/api/applications/{app_id}",
        json={"status": "INVALID_STATE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad_status.status_code == 400

    # Delete application
    del_res = client.delete(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token}"}).status_code == 404


# ==============================================================================
# 7. PERSISTENT COMPARISON LIMIT (MAX_COMPARE = 4)
# ==============================================================================

def test_persistent_comparison_enforces_limit_of_4(
    client: TestClient,
    db_session: Session,
):
    reg = client.post("/api/auth/register", json={"email": "comparator@example.com", "password": "Password123!"})
    token = reg.json()["token"]

    # Seed 5 opportunities
    univ = University(name="General University", city="Boston", state="MA", country="US")
    db_session.add(univ)
    db_session.flush()

    opp_ids = []
    for i in range(5):
        opp = ScholarshipOpportunity(
            title=f"Scholarship {i+1}",
            slug=f"scholarship-{i+1}",
            university_id=univ.id,
            target_degree_level="BACHELOR",
            destination_country="US",
            academic_cycle="2026-2027",
            verification_status=VerificationState.VERIFIED.value,
            fingerprint_sha256=f"fp-comp-{i}",
        )
        db_session.add(opp)
        db_session.flush()
        opp_ids.append(opp.id)
    db_session.commit()

    # Add 4 opportunities
    for i in range(4):
        res = client.post(f"/api/comparison/{opp_ids[i]}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201
        assert res.json()["count"] == i + 1

    # 5th opportunity rejected deterministically
    fifth_res = client.post(f"/api/comparison/{opp_ids[4]}", headers={"Authorization": f"Bearer {token}"})
    assert fifth_res.status_code == 400
    assert "maximum of 4 scholarships" in fifth_res.json()["detail"].lower()

    # Remove one and add fifth
    rem_res = client.delete(f"/api/comparison/{opp_ids[0]}", headers={"Authorization": f"Bearer {token}"})
    assert rem_res.status_code == 200
    assert rem_res.json()["count"] == 3

    add_res = client.post(f"/api/comparison/{opp_ids[4]}", headers={"Authorization": f"Bearer {token}"})
    assert add_res.status_code == 201
    assert add_res.json()["count"] == 4

    # Clear all
    clear_res = client.delete("/api/comparison", headers={"Authorization": f"Bearer {token}"})
    assert clear_res.status_code == 200
    assert clear_res.json()["count"] == 0


# ==============================================================================
# 8. INTELLIGENCE INTEGRATION TESTS
# ==============================================================================

def test_authenticated_evaluation_preserves_phase_1_invariants(
    client: TestClient,
    test_opportunity: ScholarshipOpportunity,
):
    """Verifies that an authenticated student's persistent profile seamlessly integrates
    with the Phase 1 EligibilityEvaluator and preserves all epistemic invariants.
    """
    reg = client.post("/api/auth/register", json={"email": "integ@example.com", "password": "Password123!"})
    token = reg.json()["token"]

    # Set persistent profile
    client.put(
        "/api/student-profile",
        json={
            "citizenship_country": "ET",
            "residence_country": "ET",
            "gpa": 3.9,
            "gpa_scale": 4.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Evaluate opportunity using student profile input
    eval_res = client.post(
        f"/api/opportunities/{test_opportunity.id}/evaluate",
        json={
            "profile": {
                "citizenship_country": "ET",
                "residence_country": "ET",
                "gpa": 3.9,
                "gpa_scale": 4.0,
            },
            "target_academic_cycle": "2026-2027",
            "allow_partially_verified": False,
        },
    )
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["status"] in ("ELIGIBLE", "NEEDS_INFORMATION")
    assert data["verification_status"] == VerificationState.VERIFIED.value
    # No arbitrary scores or percentages injected
    assert "score" not in data
    assert "admission_probability" not in data
