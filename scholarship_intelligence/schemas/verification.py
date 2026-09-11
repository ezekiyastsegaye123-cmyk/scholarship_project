"""Pydantic schemas for verification records and conflicting evidence logs."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import ConflictStatus, VerificationState


class VerificationRecordBase(BaseModel):
    verification_state: VerificationState = Field(default=VerificationState.UNVERIFIED)
    verifier_identity: str = Field(..., min_length=2, max_length=100)
    verification_method: str = Field(..., min_length=2, max_length=100)
    evidence_url: str = Field(..., min_length=5, max_length=1000)
    evidence_quote: str = Field(..., min_length=2, description="Verbatim citation supporting the verification")
    notes: Optional[str] = None
    verified_at: Optional[datetime] = None


class VerificationRecordCreate(VerificationRecordBase):
    pass


class VerificationRecordRead(VerificationRecordBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)


class ConflictRecordBase(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=100)
    source_a_value: str = Field(..., min_length=1)
    source_a_url: str = Field(..., min_length=5, max_length=1000)
    source_b_value: str = Field(..., min_length=1)
    source_b_url: str = Field(..., min_length=5, max_length=1000)
    resolution_status: ConflictStatus = Field(default=ConflictStatus.OPEN)
    resolution_notes: Optional[str] = None
    recorded_at: Optional[datetime] = None


class ConflictRecordCreate(ConflictRecordBase):
    pass


class ConflictRecordRead(ConflictRecordBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)
