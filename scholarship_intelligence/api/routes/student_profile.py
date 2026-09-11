"""Student profile validation and management endpoints."""
import uuid
from fastapi import APIRouter, HTTPException

from scholarship_intelligence.api.schemas import StudentProfileInput

router = APIRouter(prefix="/student-profile", tags=["Student Profile"])


@router.post("", response_model=StudentProfileInput)
def validate_and_save_profile(profile: StudentProfileInput):
    """Validates and returns a privacy-preserving student profile.

    Enforces data minimization:
    - Rejects sensitive documents, SSNs, bank details, and passwords.
    - Preserves unprovided fields as UNKNOWN/None (zero fabrication).
    """
    if not profile.id:
        profile.id = f"std-{uuid.uuid4().hex[:8]}"
    return profile
