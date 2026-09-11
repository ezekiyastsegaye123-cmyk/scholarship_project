"""Pydantic schemas for verification records, conflicting evidence logs, and Phase 1C verification pipeline."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    ConflictStatus,
    LivenessStatus,
    QuarantineReason,
    VerificationState,
)
from scholarship_intelligence.schemas.candidate import CandidateEvidence


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
    source_a_tier: Optional[AuthorityTier] = None
    source_b_tier: Optional[AuthorityTier] = None
    source_a_evidence: Optional[str] = None
    source_b_evidence: Optional[str] = None
    resolution_status: ConflictStatus = Field(default=ConflictStatus.OPEN)
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    recorded_at: Optional[datetime] = None


class ConflictRecordCreate(ConflictRecordBase):
    pass


class ConflictRecordRead(ConflictRecordBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)


class SourceLivenessResult(BaseModel):
    """Result of a deterministic source liveness and soft-404 inspection."""
    source_url: str
    liveness_status: LivenessStatus
    http_status: Optional[int] = None
    final_url: Optional[str] = None
    redirect_chain: List[str] = Field(default_factory=list)
    content_sha256: Optional[str] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    is_live: bool = False
    is_soft_404: bool = False
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceLivenessLogRead(BaseModel):
    id: str
    scholarship_id: Optional[str] = None
    source_url: str
    liveness_status: str
    http_status: Optional[int] = None
    final_url: Optional[str] = None
    redirect_chain_json: Optional[str] = None
    content_sha256: Optional[str] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    checked_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VerificationHistoryBase(BaseModel):
    scholarship_id: str
    field_name: str = Field(..., min_length=1, max_length=100)
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    old_evidence_url: Optional[str] = None
    old_evidence_quote: Optional[str] = None
    new_evidence_url: Optional[str] = None
    new_evidence_quote: Optional[str] = None
    decision: str = Field(..., min_length=2, max_length=50)
    reason: str = Field(..., min_length=2)
    changed_at: Optional[datetime] = None


class VerificationHistoryCreate(VerificationHistoryBase):
    pass


class VerificationHistoryRead(VerificationHistoryBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class FactVerificationResult(BaseModel):
    """Fine-grained verification outcome for an individual scholarship fact."""
    field_name: str
    candidate_value: Any
    canonical_value: Optional[Any] = None
    verification_state: VerificationState
    supporting_evidence: Optional[CandidateEvidence] = None
    authority_tier: Optional[AuthorityTier] = None
    notes: Optional[str] = None
    is_conflict: bool = False
    conflict_record: Optional[ConflictRecordCreate] = None


class VerificationDecisionResult(BaseModel):
    """Aggregate outcome of Phase 1C verification process."""
    overall_state: VerificationState
    opportunity_title: str
    academic_cycle: str
    facts: List[FactVerificationResult] = Field(default_factory=list)
    conflicts: List[ConflictRecordCreate] = Field(default_factory=list)
    quarantine_reasons: List[QuarantineReason] = Field(default_factory=list)
    liveness_result: Optional[SourceLivenessResult] = None
    rationale: str
    can_promote: bool = False
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

