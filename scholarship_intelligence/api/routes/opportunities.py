"""Opportunity discovery and detail endpoints."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from scholarship_intelligence.api.schemas import OpportunityDetail, PaginatedOpportunities, VerificationHistoryItem
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.db.session import get_db_session

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])
service = ApiService()


def get_db():
    with get_db_session() as session:
        yield session


@router.get("", response_model=PaginatedOpportunities)
def list_opportunities(
    search: Optional[str] = Query(None, max_length=100, description="Search across title, description, university, provider"),
    degree_level: Optional[str] = Query(None, max_length=50),
    international_allowed: Optional[str] = Query(None, max_length=20),
    provider: Optional[str] = Query(None, max_length=100),
    university: Optional[str] = Query(None, max_length=100),
    funding_type: Optional[str] = Query(None, max_length=50),
    verification_status: Optional[str] = Query(None, max_length=50),
    deadline_status: Optional[str] = Query(None, max_length=20),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(10, ge=1, le=100),
    order_by: str = Query("deadline", pattern="^(deadline|title|university)$"),
    reference_date: Optional[date] = Query(None, description="Deterministic reference date (defaults to 2026-11-01)"),
    db: Session = Depends(get_db),
):
    """List, search, filter, and paginate scholarship opportunities."""
    return service.list_opportunities(
        session=db,
        search=search,
        degree_level=degree_level,
        international_allowed=international_allowed,
        provider=provider,
        university=university,
        funding_type=funding_type,
        verification_status=verification_status,
        deadline_status=deadline_status,
        page=page,
        page_size=page_size,
        order_by=order_by,
        reference_date=reference_date,
    )


@router.get("/{opportunity_id}/verification-history", response_model=list[VerificationHistoryItem])
def get_verification_history(
    opportunity_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve complete audit trail of fact modifications and re-verifications for an opportunity."""
    return service.get_verification_history(session=db, opportunity_id=opportunity_id)


@router.get("/{opportunity_id}", response_model=OpportunityDetail)
def get_opportunity(
    opportunity_id: str,
    reference_date: Optional[date] = Query(None, description="Deterministic reference date"),
    db: Session = Depends(get_db),
):
    """Retrieve complete opportunity detail including all evidence, deadlines, and rules."""
    try:
        return service.get_opportunity_detail(
            session=db,
            opportunity_id=opportunity_id,
            reference_date=reference_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
