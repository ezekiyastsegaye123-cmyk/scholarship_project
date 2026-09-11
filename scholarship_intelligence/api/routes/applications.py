"""API endpoints for student application tracking."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import get_current_account, get_db
from scholarship_intelligence.api.schemas import (
    ApplicationRecordCreate,
    ApplicationRecordItem,
    ApplicationRecordUpdate,
    PaginatedApplications,
)
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.models.student_account import StudentAccount

router = APIRouter(prefix="/applications", tags=["Application Tracking"])
service = ApiService()


@router.post("", response_model=ApplicationRecordItem, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationRecordCreate,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Creates a new application tracking record for an opportunity."""
    return service.create_application(session=db, account_id=current_account.id, data=payload)


@router.get("", response_model=PaginatedApplications)
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Retrieves paginated application tracking records for the authenticated student."""
    return service.list_applications(session=db, account_id=current_account.id, page=page, page_size=page_size)


@router.get("/{application_id}", response_model=ApplicationRecordItem)
def get_application(
    application_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Retrieves an application tracking record with ownership enforcement."""
    return service.get_application(session=db, account_id=current_account.id, application_id=application_id)


@router.patch("/{application_id}", response_model=ApplicationRecordItem)
def update_application(
    application_id: str,
    payload: ApplicationRecordUpdate,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Updates status, student notes, or submission date on an application record."""
    return service.update_application(
        session=db,
        account_id=current_account.id,
        application_id=application_id,
        update=payload,
    )


@router.delete("/{application_id}")
def delete_application(
    application_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Removes an application tracking record with ownership enforcement."""
    service.delete_application(session=db, account_id=current_account.id, application_id=application_id)
    return {"status": "success", "message": "Application record deleted."}
