"""Pydantic schemas for scholarship and admission deadlines."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import DeadlineType


class DeadlineBase(BaseModel):
    deadline_type: DeadlineType
    deadline_date: Optional[date] = None
    is_exact_date: bool = True
    timezone: Optional[str] = Field("America/New_York", max_length=50)
    academic_cycle: str = Field("2026-2027", max_length=20)
    varies_by_program: bool = False
    context_description: Optional[str] = None
    source_evidence_snippet: Optional[str] = None


class DeadlineCreate(DeadlineBase):
    pass


class DeadlineRead(DeadlineBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)
