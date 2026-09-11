"""API endpoints for ingestion runs and sources management."""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from scholarship_intelligence.api.dependencies import get_db
from scholarship_intelligence.api.schemas import IngestionRunItem, IngestionSourceItem
from scholarship_intelligence.api.service import ApiService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])
service = ApiService()


@router.get("/runs", response_model=List[IngestionRunItem])
def list_ingestion_runs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List past ingestion execution runs and summary metrics."""
    return service.list_ingestion_runs(session=db, limit=limit)


@router.get("/sources", response_model=List[IngestionSourceItem])
def list_ingestion_sources(
    db: Session = Depends(get_db),
):
    """List registered ingestion sources, authority tiers, and crawl statuses."""
    return service.list_ingestion_sources(session=db)
