"""FastAPI request dependencies for database sessions and authentication."""
from typing import Generator, Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from scholarship_intelligence.auth.security import AuthenticationError, decode_access_token
from scholarship_intelligence.db.session import get_db_session
from scholarship_intelligence.models.student_account import StudentAccount


def get_db() -> Generator[Session, None, None]:
    """Provides transactional database session for request lifecycle."""
    with get_db_session() as session:
        yield session


def get_token_from_request(
    authorization: Optional[str] = Header(None, description="Bearer token header"),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
) -> Optional[str]:
    """Extracts authentication token from Authorization header or HttpOnly cookie."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    if access_token_cookie:
        return access_token_cookie
    return None


def get_current_account(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db),
) -> StudentAccount:
    """Enforces authentication and returns authenticated StudentAccount principal.
    
    Raises 401 Unauthorized if missing, expired, or invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    account_id = payload.get("sub")
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account = db.query(StudentAccount).filter(
        StudentAccount.id == account_id,
        StudentAccount.is_active == True,
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return account


def get_optional_current_account(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db),
) -> Optional[StudentAccount]:
    """Optionally returns authenticated StudentAccount or None if unauthenticated."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        account_id = payload.get("sub")
        if not account_id:
            return None
        return db.query(StudentAccount).filter(
            StudentAccount.id == account_id,
            StudentAccount.is_active == True,
        ).first()
    except Exception:
        return None
