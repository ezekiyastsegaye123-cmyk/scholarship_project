"""API request and response DTO schemas for Phase 2 Student MVP."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scholarship_intelligence.domain.enums import (
    DeadlineType,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult

FORBIDDEN_PRIVACY_FIELDS = {
    "password",
    "password_hash",
    "ssn",
    "social_security_number",
    "bank_account",
    "bank_routing",
    "credit_card",
    "cvv",
    "tax_return_pdf",
    "national_id",
    "passport_scan",
    "profile_vector",
    "embedding",
}


class OpportunitySummary(BaseModel):
    """Concise representation of an opportunity for discovery cards and lists."""
    id: str
    title: str
    slug: str
    provider_name: Optional[str] = None
    university_name: Optional[str] = None
    target_degree_level: str = "BACHELOR"
    destination_country: str = "US"
    academic_cycle: str = "2026-2027"
    verification_status: VerificationState
    funding_classification: FundingClassification
    funding_summary: str
    earliest_deadline: Optional[date] = None
    deadline_type: Optional[DeadlineType] = None
    deadline_status: str = "UNKNOWN"
    international_students_allowed: TriState = TriState.UNKNOWN
    requires_sat: TriState = TriState.UNKNOWN
    requires_act: TriState = TriState.UNKNOWN
    financial_need_required: TriState = TriState.UNKNOWN
    primary_source_url: Optional[str] = None
    freshness_level: Optional[str] = "UNVERIFIED"
    freshness_message: Optional[str] = None
    last_crawled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityDetail(OpportunitySummary):
    """Complete detail view of an opportunity with all evidence and relations."""
    description: Optional[str] = None
    varies_by_program: bool = False
    requires_css_profile: TriState = TriState.UNKNOWN
    fingerprint_sha256: str
    
    # Detailed nested structures
    award_details: Optional[Dict[str, Any]] = None
    deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    eligibility_rules: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    application_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    official_sources: List[Dict[str, Any]] = Field(default_factory=list)
    discovery_sources: List[Dict[str, Any]] = Field(default_factory=list)
    verification_records: List[Dict[str, Any]] = Field(default_factory=list)
    conflict_records: List[Dict[str, Any]] = Field(default_factory=list)
    verification_histories: List[Dict[str, Any]] = Field(default_factory=list)


class VerificationHistoryItem(BaseModel):
    """Audit entry for canonical fact modifications."""
    id: str
    scholarship_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    old_evidence_url: Optional[str] = None
    old_evidence_quote: Optional[str] = None
    new_evidence_url: Optional[str] = None
    new_evidence_quote: Optional[str] = None
    decision: str
    reason: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestionSourceItem(BaseModel):
    """Registered source metadata."""
    id: str
    name: str
    url: str
    source_domain: str
    authority_tier: str
    is_active: bool
    fetch_interval_hours: int
    last_crawled_at: Optional[datetime] = None
    last_content_sha256: Optional[str] = None
    last_http_status: Optional[int] = None
    failure_count: int = 0
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IngestionRunItem(BaseModel):
    """Execution metrics of an ingestion run."""
    id: str
    run_type: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    sources_attempted: int
    sources_succeeded: int
    sources_failed: int
    opportunities_scanned: int
    opportunities_updated: int
    opportunities_created: int
    conflicts_detected: int
    error_log_json: Optional[str] = None
    reference_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedOpportunities(BaseModel):
    """Pagination wrapper for opportunity listing."""
    items: List[OpportunitySummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentProfileInput(BaseModel):
    """Privacy-preserving student profile input."""
    id: Optional[str] = None
    citizenship_country: str = Field(..., min_length=2, max_length=3)
    residence_country: str = Field(..., min_length=2, max_length=3)
    intended_degree_level: str = Field("BACHELOR", description="MVP is strictly scoped to BACHELOR")
    intended_destination_country: str = Field("US", description="MVP is strictly scoped to US")
    
    gpa: Optional[float] = Field(None, ge=0.0, le=100.0)
    gpa_scale: Optional[float] = Field(4.0, ge=1.0, le=100.0)
    intended_major: Optional[str] = None
    english_test_type: Optional[str] = None
    english_test_score: Optional[float] = None
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    act_score: Optional[int] = Field(None, ge=1, le=36)
    
    financial_need_tier: Optional[str] = Field(
        None, description="Broad self-reported tier: HIGH, MODERATE, LOW, NONE"
    )
    
    # Application materials explicitly prepared by student (no inferred completion)
    prepared_materials: List[str] = Field(default_factory=list)
    academic_achievements: List[str] = Field(default_factory=list)
    extracurricular_activities: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_privacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for forbidden in FORBIDDEN_PRIVACY_FIELDS:
                if forbidden in data:
                    raise ValueError(f"Privacy violation: field '{forbidden}' is strictly forbidden in StudentProfile")
        return data


class EvaluationRequest(BaseModel):
    """Request payload for deterministic eligibility evaluation."""
    profile: StudentProfileInput
    target_academic_cycle: str = "2026-2027"
    allow_partially_verified: bool = False
    evaluated_at: Optional[datetime] = None


class CounselRequest(BaseModel):
    """Request payload for multi-dimensional qualitative counselor assessment."""
    profile: StudentProfileInput
    target_academic_cycle: str = "2026-2027"
    reference_date: Optional[date] = None
    evaluated_at: Optional[datetime] = None


class ComparisonRequest(BaseModel):
    """Request payload for comparing up to 10 opportunities."""
    opportunity_ids: List[str] = Field(..., min_length=1, max_length=10)
    profile: Optional[StudentProfileInput] = None
    target_academic_cycle: str = "2026-2027"
    reference_date: Optional[date] = None
    evaluated_at: Optional[datetime] = None


class ComparisonItem(BaseModel):
    """Structured dimension-by-dimension comparison item (no composite score)."""
    opportunity_id: str
    opportunity_title: str
    provider_name: Optional[str] = None
    university_name: Optional[str] = None
    verification_status: VerificationState
    funding_classification: FundingClassification
    funding_summary: str
    earliest_deadline: Optional[date] = None
    deadline_status: str
    primary_source_url: Optional[str] = None
    
    # Contextual evaluations (populated when profile is supplied)
    eligibility_status: Optional[str] = None
    eligibility_summary: Optional[str] = None
    academic_alignment: Optional[str] = None
    geographic_alignment: Optional[str] = None
    program_alignment: Optional[str] = None
    testing_readiness: Optional[str] = None
    application_readiness: Optional[str] = None


class ComparisonResponse(BaseModel):
    """Comparison matrix result with transparent ordering rules."""
    items: List[ComparisonItem]
    ordering_rule: str = "Ordered by requested selection order, then earliest deadline, then title"
    total_compared: int
