"""Student profile validation and persistent management endpoints."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import (
    get_current_account,
    get_db,
    get_optional_current_account,
)
from scholarship_intelligence.api.schemas import (
    PersistentProfileResponse,
    PersistentProfileUpdate,
    StudentProfileInput,
)
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.models.student_account import StudentAccount

router = APIRouter(prefix="/student-profile", tags=["Student Profile"])
service = ApiService()


@router.get("", response_model=PersistentProfileResponse)
def get_persistent_profile(
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Retrieves the authenticated student's persistent profile."""
    return service.get_persistent_profile(session=db, account_id=current_account.id)


@router.put("", response_model=PersistentProfileResponse)
def update_persistent_profile(
    payload: PersistentProfileUpdate,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Updates the authenticated student's persistent profile with strict privacy validation."""
    return service.update_persistent_profile(
        session=db,
        account_id=current_account.id,
        update=payload,
    )


@router.post("", response_model=StudentProfileInput)
def validate_profile(
    profile: StudentProfileInput,
    current_account: Optional[StudentAccount] = Depends(get_optional_current_account),
    db: Session = Depends(get_db),
):
    """Validates and returns a privacy-preserving student profile.

    Supports both anonymous validation (Phase 2 backward compatibility)
    and optional sync for authenticated accounts.
    """
    if not profile.id:
        profile.id = f"std-{uuid.uuid4().hex[:8]}"

    if current_account:
        # Sync changes to persistent profile if logged in
        update_data = PersistentProfileUpdate(
            citizenship_country=profile.citizenship_country,
            residence_country=profile.residence_country,
            intended_degree_level=profile.intended_degree_level,
            intended_destination_country=profile.intended_destination_country,
            gpa=profile.gpa,
            gpa_scale=profile.gpa_scale,
            intended_major=profile.intended_major,
            english_test_type=profile.english_test_type,
            english_test_score=profile.english_test_score,
            sat_score=profile.sat_score,
            act_score=profile.act_score,
            financial_need_tier=profile.financial_need_tier,
            academic_achievements=profile.academic_achievements,
            extracurricular_activities=profile.extracurricular_activities,
            interests=profile.interests,
        )
        service.update_persistent_profile(session=db, account_id=current_account.id, update=update_data)

    return profile
