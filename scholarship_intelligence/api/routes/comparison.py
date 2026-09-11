"""API endpoints for persistent student comparison selections."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import get_current_account, get_db
from scholarship_intelligence.api.schemas import PersistentComparisonResponse
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.models.student_account import StudentAccount

router = APIRouter(prefix="/comparison", tags=["Comparison Selections"])
service = ApiService()


@router.get("", response_model=PersistentComparisonResponse)
def list_comparisons(
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Lists currently selected opportunities for comparison (max 4)."""
    return service.list_comparison_selections(session=db, account_id=current_account.id)


@router.post("/{opportunity_id}", response_model=PersistentComparisonResponse, status_code=status.HTTP_201_CREATED)
def add_comparison(
    opportunity_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Adds an opportunity to comparison set, enforcing MAX_COMPARE = 4."""
    return service.add_comparison_selection(
        session=db,
        account_id=current_account.id,
        opportunity_id=opportunity_id,
    )


@router.delete("/{opportunity_id}", response_model=PersistentComparisonResponse)
def remove_comparison(
    opportunity_id: str,
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Removes an opportunity from the persistent comparison set."""
    return service.remove_comparison_selection(
        session=db,
        account_id=current_account.id,
        opportunity_id=opportunity_id,
    )


@router.delete("", response_model=PersistentComparisonResponse)
def clear_comparisons(
    current_account: StudentAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Clears all comparison selections for the student."""
    return service.clear_comparison_selections(session=db, account_id=current_account.id)
