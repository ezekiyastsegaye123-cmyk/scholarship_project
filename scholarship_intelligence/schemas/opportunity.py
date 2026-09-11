"""Pydantic schemas for canonical ScholarshipOpportunity records."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import TriState, VerificationState
from scholarship_intelligence.schemas.application_requirement import (
    ApplicationRequirementCreate,
    ApplicationRequirementRead,
)
from scholarship_intelligence.schemas.deadline import DeadlineCreate, DeadlineRead
from scholarship_intelligence.schemas.eligibility import (
    EligibilityRuleCreate,
    EligibilityRuleRead,
    RequirementCreate,
    RequirementRead,
)
from scholarship_intelligence.schemas.funding import AwardCreate, AwardRead
from scholarship_intelligence.schemas.source import (
    DiscoverySourceCreate,
    DiscoverySourceRead,
    OfficialSourceCreate,
    OfficialSourceRead,
)
from scholarship_intelligence.schemas.verification import (
    ConflictRecordCreate,
    ConflictRecordRead,
    VerificationRecordCreate,
    VerificationRecordRead,
)


class ScholarshipOpportunityBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    target_degree_level: str = Field("BACHELOR", description="MVP strictly scoped to BACHELOR")
    destination_country: str = Field("US", description="MVP strictly scoped to US")
    academic_cycle: str = Field("2026-2027", max_length=20)
    varies_by_program: bool = False
    
    # Explicit TriState semantic fields
    international_students_allowed: TriState = Field(
        default=TriState.UNKNOWN,
        description="Must be YES for international undergraduate access. UNKNOWN != NO."
    )
    requires_sat: TriState = Field(default=TriState.UNKNOWN)
    requires_act: TriState = Field(default=TriState.UNKNOWN)
    requires_css_profile: TriState = Field(default=TriState.UNKNOWN)
    financial_need_required: TriState = Field(default=TriState.UNKNOWN)
    
    # Explicit verification state (No arbitrary trust scores)
    verification_status: VerificationState = Field(default=VerificationState.UNVERIFIED)
    
    # Deterministic fingerprint for idempotency & deduplication
    fingerprint_sha256: Optional[str] = None


class ScholarshipOpportunityCreate(ScholarshipOpportunityBase):
    provider_id: Optional[str] = None
    university_id: Optional[str] = None
    
    # Embedded nested data for transactional creation
    official_sources: List[OfficialSourceCreate] = Field(default_factory=list)
    discovery_sources: List[DiscoverySourceCreate] = Field(default_factory=list)
    eligibility_rules: List[EligibilityRuleCreate] = Field(default_factory=list)
    requirements: List[RequirementCreate] = Field(default_factory=list)
    award: Optional[AwardCreate] = None
    deadlines: List[DeadlineCreate] = Field(default_factory=list)
    verification_records: List[VerificationRecordCreate] = Field(default_factory=list)
    conflict_records: List[ConflictRecordCreate] = Field(default_factory=list)
    application_requirements: List[ApplicationRequirementCreate] = Field(default_factory=list)


class ScholarshipOpportunityRead(ScholarshipOpportunityBase):
    id: str
    provider_id: Optional[str] = None
    university_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    official_sources: List[OfficialSourceRead] = Field(default_factory=list)
    discovery_sources: List[DiscoverySourceRead] = Field(default_factory=list)
    eligibility_rules: List[EligibilityRuleRead] = Field(default_factory=list)
    requirements: List[RequirementRead] = Field(default_factory=list)
    award: Optional[AwardRead] = None
    deadlines: List[DeadlineRead] = Field(default_factory=list)
    verification_records: List[VerificationRecordRead] = Field(default_factory=list)
    conflict_records: List[ConflictRecordRead] = Field(default_factory=list)
    application_requirements: List[ApplicationRequirementRead] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
