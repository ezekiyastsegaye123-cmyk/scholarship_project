"""Eligibility evaluation and counselor assessment endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from scholarship_intelligence.api.schemas import (
    ComparisonRequest,
    ComparisonResponse,
    CounselRequest,
    EvaluationRequest,
)
from scholarship_intelligence.api.service import ApiService
from scholarship_intelligence.db.session import get_db_session
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult

router = APIRouter(tags=["Evaluation & Counselor"])
service = ApiService()


def get_db():
    with get_db_session() as session:
        yield session


@router.post("/opportunities/{opportunity_id}/evaluate", response_model=EligibilityEvaluationResult)
def evaluate_opportunity(
    opportunity_id: str,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
):
    """Deterministically evaluates student eligibility against an opportunity using Phase 1 engine."""
    try:
        return service.evaluate_opportunity(
            session=db,
            opportunity_id=opportunity_id,
            profile=payload.profile,
            target_academic_cycle=payload.target_academic_cycle,
            allow_partially_verified=payload.allow_partially_verified,
            evaluated_at=payload.evaluated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/opportunities/{opportunity_id}/counsel", response_model=CounselorAssessmentResult)
def counsel_opportunity(
    opportunity_id: str,
    payload: CounselRequest,
    db: Session = Depends(get_db),
):
    """Generates a complete qualitative counselor assessment using Phase 1 counselor service."""
    try:
        return service.counsel_opportunity(
            session=db,
            opportunity_id=opportunity_id,
            profile=payload.profile,
            target_academic_cycle=payload.target_academic_cycle,
            reference_date=payload.reference_date,
            evaluated_at=payload.evaluated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/compare", response_model=ComparisonResponse)
def compare_opportunities(
    payload: ComparisonRequest,
    db: Session = Depends(get_db),
):
    """Compares up to 10 opportunities across transparent factual dimensions without composite scoring."""
    if len(payload.opportunity_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 opportunities can be compared at once.")

    return service.compare_opportunities(
        session=db,
        opportunity_ids=payload.opportunity_ids,
        profile=payload.profile,
        target_academic_cycle=payload.target_academic_cycle,
        reference_date=payload.reference_date,
        evaluated_at=payload.evaluated_at,
    )
