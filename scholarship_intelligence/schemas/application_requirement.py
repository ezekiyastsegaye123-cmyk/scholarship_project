"""Pydantic schemas for student application preparation items."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import RequirementKind, RequirementType


class ApplicationRequirementBase(BaseModel):
    requirement_type: RequirementType
    kind: RequirementKind = Field(default=RequirementKind.REQUIRED)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    submission_format: Optional[str] = None
    source_evidence_snippet: Optional[str] = None


class ApplicationRequirementCreate(ApplicationRequirementBase):
    pass


class ApplicationRequirementRead(ApplicationRequirementBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)
