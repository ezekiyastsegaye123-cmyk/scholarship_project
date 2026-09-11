"""Tests enforcing strict Privacy-by-Design and Data Minimization.

Verifies:
- Zero passwords, SSNs, national ID card scans, or banking credentials in StudentProfile.
- Zero profile vectors, embeddings, or recommendation match scores in Phase 1A.
"""
import pytest
from pydantic import ValidationError

from scholarship_intelligence.models.student_profile import StudentProfile
from scholarship_intelligence.schemas.student_profile import (
    FORBIDDEN_PRIVACY_FIELDS,
    StudentProfileCreate,
)


def test_forbidden_fields_rejected_by_schema():
    """Enforces that forbidden PII and vector fields are rejected with a ValueError."""
    for forbidden in FORBIDDEN_PRIVACY_FIELDS:
        payload = {
            "citizenship_country": "GH",
            "residence_country": "GH",
            forbidden: "sensitive_data_value",
        }
        with pytest.raises(ValidationError, match=f"Privacy violation: field '{forbidden}' is strictly forbidden"):
            StudentProfileCreate(**payload)


def test_database_model_has_no_forbidden_columns():
    """Enforces that the SQLAlchemy StudentProfile table does not contain forbidden columns."""
    column_names = {c.name for c in StudentProfile.__table__.columns}
    for forbidden in FORBIDDEN_PRIVACY_FIELDS:
        assert forbidden not in column_names, f"Forbidden column '{forbidden}' found in StudentProfile model!"

    # Extra checks for vector/embedding keywords
    assert "profile_vector" not in column_names
    assert "embedding" not in column_names
    assert "embedding_768" not in column_names
    assert "match_score" not in column_names
