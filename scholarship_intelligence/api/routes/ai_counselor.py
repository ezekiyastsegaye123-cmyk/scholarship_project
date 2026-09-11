"""API route for the grounded AI Scholarship Counselor."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from scholarship_intelligence.ai.rate_limiter import ai_rate_limiter
from scholarship_intelligence.ai.schemas import AICounselorRequest, AICounselorResponse
from scholarship_intelligence.ai.service import AICounselorService
from scholarship_intelligence.api.dependencies import get_current_account, get_db
from scholarship_intelligence.models.student_account import StudentAccount
from scholarship_intelligence.models.student_profile import StudentProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Counselor"])
counselor_service = AICounselorService()


@router.post("/counsel", response_model=AICounselorResponse)
def ask_ai_counselor(
    payload: AICounselorRequest,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Answers student questions grounded exclusively in verified scholarship facts and student profile.

    Strict Constraints:
    - Guaranteed zero admission/winning probabilities.
    - Guaranteed zero ranking scores.
    - Full fallback to deterministic guidance on model failure.
    - Epistemic invariants preserved (UNKNOWN != NO, FULL_TUITION != FULL_FUNDING).
    - Hard rate limiting per student account.
    """
    # 1. Rate limiting check
    allowed, remaining, retry_after = ai_rate_limiter.is_allowed(str(current_account.id))
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # 2. Retrieve authenticated student's profile (IDOR defense: profile is strictly scoped to current_account)
    profile = (
        current_account.profile
        or db.query(StudentProfile).filter(StudentProfile.account_id == current_account.id).first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile has not been created yet. Please complete your profile first.",
        )

    # 3. Invoke AI counselor
    try:
        response = counselor_service.counsel_opportunity(
            session=db,
            opportunity_id=payload.opportunity_id,
            student_profile=profile,
            user_message=payload.message,
            conversation_history=payload.conversation_history,
        )
        return response
    except ValueError as val_err:
        err_msg = str(val_err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as exc:
        logger.error("AI counselor processing error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating counselor guidance.",
        )
