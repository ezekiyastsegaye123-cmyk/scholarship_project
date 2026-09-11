"""API endpoints for student saved scholarship opportunities."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import get_current_account, get_db
from scholarship_intelligence.api.schemas import PaginatedSavedOpportunities, SavedOpportunityItem
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.models.student_account import StudentAccount

router = APIRouter(prefix="/saved-opportunities", tags=["Saved Scholarships"])
service = ApiService()


@router.post("/{opportunity_id}", response_model=SavedOpportunityItem, status_code=status.HTTP_201_CREATED)
def save_opportunity(
    opportunity_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Saves an authentic scholarship opportunity reference for the authenticated student."""
    return service.save_opportunity(session=db, account_id=current_account.id, opportunity_id=opportunity_id)


@router.delete("/{opportunity_id}")
def unsave_opportunity(
    opportunity_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Removes a saved scholarship opportunity reference for the authenticated student."""
    service.unsave_opportunity(session=db, account_id=current_account.id, opportunity_id=opportunity_id)
    return {"status": "success", "message": "Opportunity removed from saved list."}


@router.get("", response_model=PaginatedSavedOpportunities)
def list_saved_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Retrieves paginated saved opportunities for the authenticated student with current canonical intelligence."""
    return service.list_saved_opportunities(
        session=db,
        account_id=current_account.id,
        page=page,
        page_size=page_size,
    )
