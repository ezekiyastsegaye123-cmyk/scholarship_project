"""Authentication API endpoints for student accounts."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import get_current_account, get_db
from scholarship_intelligence.api.schemas import AuthResponse, LoginRequest, RegisterRequest, StudentAccountItem
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.models.student_account import StudentAccount

router = APIRouter(prefix="/auth", tags=["Authentication"])
service = ApiService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Registers a new student account transactionally with default profile."""
    result = service.register_account(session=db, email=payload.email, password=payload.password)
    # Set HttpOnly session cookie for enhanced browser security
    response.set_cookie(
        key="access_token",
        value=result.token,
        httponly=True,
        samesite="lax",
        secure=False,  # Can be configured via environment for HTTPS
        max_age=72 * 3600,
    )
    return result


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticates student credentials and returns an access session token."""
    result = service.login_account(session=db, email=payload.email, password=payload.password)
    response.set_cookie(
        key="access_token",
        value=result.token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=72 * 3600,
    )
    return result


@router.post("/logout")
def logout(
    response: Response,
    current_account: StudentAccount = Depends(get_current_account),
):
    """Invalidates the authenticated session by clearing authentication cookies."""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me", response_model=StudentAccountItem)
def get_current_user_me(
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Returns safe identity representation of currently authenticated student."""
    return service.get_me(session=db, account=current_account)
