"""Candidate models for Phase 1B evidence staging.

These schemas represent unverified extracted facts staged with source evidence.
They strictly model candidate data and do NOT represent verified canonical records.
"""
from datetime import date, datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    RequirementType,
    RuleKind,
    TriState,
)
from scholarship_intelligence.ingestion.status import FetchResult


class CandidateEvidence(BaseModel):
    """Immutable provenance anchor for an extracted candidate fact."""
    model_config = ConfigDict(frozen=True)

    source_url: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    http_status: int = 200
    content_sha256: str
    evidence_text: str = Field(
        ...,
        min_length=1,
        description="Concise excerpt or snippet supporting the candidate fact. Never full page dump.",
    )
    evidence_context: Optional[str] = Field(
        default=None,
        description="Structural context e.g. section heading, table header, or element path.",
    )
    authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY


class CandidateFundingComponent(BaseModel):
    """Decomposed funding component extracted from institutional webpage."""
    component_type: FundingComponentType
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    currency: str = "USD"
    amount_period: AmountPeriod = AmountPeriod.ANNUAL
    percentage_tuition: Optional[float] = None
    description: Optional[str] = None
    evidence: CandidateEvidence


class CandidateAward(BaseModel):
    """Candidate scholarship award structure with evidence."""
    funding_classification: FundingClassification
    title: str
    is_renewable: TriState = TriState.UNKNOWN
    renewal_criteria: Optional[str] = None
    estimated_annual_value_usd: Optional[float] = None
    components: List[CandidateFundingComponent] = Field(default_factory=list)
    evidence: CandidateEvidence


class CandidateDeadline(BaseModel):
    """Candidate deadline extracted from institutional webpage."""
    deadline_type: DeadlineType
    raw_date_text: str
    deadline_date: Optional[date] = None
    is_exact_date: bool = False
    academic_cycle: Optional[str] = None
    timezone: Optional[str] = "America/New_York"
    varies_by_program: bool = False
    context_description: Optional[str] = None
    evidence: CandidateEvidence


class CandidateRequirement(BaseModel):
    """Candidate eligibility requirement extracted from webpage text or tables."""
    requirement_type: RequirementType
    kind: RuleKind = RuleKind.REQUIRED
    name: str
    raw_text: str
    field_name: Optional[str] = None
    operator: Optional[str] = None
    target_value: Optional[Any] = None
    evidence: CandidateEvidence


class CandidateOpportunity(BaseModel):
    """Candidate scholarship opportunity staged with source evidence.
    
    Represents unverified candidate findings extracted from institutional source.
    """
    title: str
    university_name: Optional[str] = None
    provider_name: Optional[str] = None
    academic_cycle: str = "2026-2027"
    target_degree_level: str = "BACHELOR"
    destination_country: str = "US"
    description: Optional[str] = None
    international_students_allowed: TriState = TriState.UNKNOWN
    requires_sat: TriState = TriState.UNKNOWN
    requires_act: TriState = TriState.UNKNOWN
    requires_css_profile: TriState = TriState.UNKNOWN
    financial_need_required: TriState = TriState.UNKNOWN
    
    award: Optional[CandidateAward] = None
    deadlines: List[CandidateDeadline] = Field(default_factory=list)
    requirements: List[CandidateRequirement] = Field(default_factory=list)
    source_evidence: List[CandidateEvidence] = Field(default_factory=list)
    
    extraction_status: str = "EXTRACTED"
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateStagingResult(BaseModel):
    """Output envelope of Phase 1B ingestion pipeline."""
    fetch_result: FetchResult
    candidate: Optional[CandidateOpportunity] = None
    evidence_items: List[CandidateEvidence] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
