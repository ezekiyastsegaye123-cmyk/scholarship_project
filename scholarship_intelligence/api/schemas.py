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
    "bankAccount",
    "bank_routing",
    "credit_card",
    "card_number",
    "cvv",
    "tax_id",
    "taxpayer_id",
    "tax_return_pdf",
    "national_id",
    "passport",
    "passport_number",
    "passport_scan",
    "profile_vector",
    "embedding",
    "secret",
    "api_key",
    "private_key",
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
            # Tolerant alias mappings for frontend convenience
            if "country_of_residence" in data and "residence_country" not in data:
                data["residence_country"] = data["country_of_residence"]
            if "degree_level" in data and "intended_degree_level" not in data:
                data["intended_degree_level"] = data["degree_level"]
            if "sat_total" in data and "sat_score" not in data:
                data["sat_score"] = data["sat_total"]
            if "act_composite" in data and "act_score" not in data:
                data["act_score"] = data["act_composite"]
            if "prepared_components" in data and "prepared_materials" not in data:
                data["prepared_materials"] = data["prepared_components"]
        return data


class EvaluationRequest(BaseModel):
    """Request payload for deterministic eligibility evaluation."""
    profile: StudentProfileInput
    target_academic_cycle: str = "2026-2027"
    allow_partially_verified: bool = False
    evaluated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def handle_profile_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "student_profile" in data and "profile" not in data:
            data["profile"] = data["student_profile"]
        return data


class CounselRequest(BaseModel):
    """Request payload for multi-dimensional qualitative counselor assessment."""
    profile: StudentProfileInput
    target_academic_cycle: str = "2026-2027"
    reference_date: Optional[date] = None
    evaluated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def handle_profile_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "student_profile" in data and "profile" not in data:
            data["profile"] = data["student_profile"]
        return data


class ComparisonRequest(BaseModel):
    """Request payload for comparing up to 10 opportunities."""
    opportunity_ids: List[str] = Field(..., min_length=1, max_length=10)
    profile: Optional[StudentProfileInput] = None
    target_academic_cycle: str = "2026-2027"
    reference_date: Optional[date] = None
    evaluated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def handle_profile_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "student_profile" in data and "profile" not in data:
            data["profile"] = data["student_profile"]
        return data


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
    comparisons: Optional[List[ComparisonItem]] = None

    @model_validator(mode="before")
    @classmethod
    def populate_comparisons_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "items" in data and "comparisons" not in data:
                data["comparisons"] = data["items"]
            elif "comparisons" in data and "items" not in data:
                data["items"] = data["comparisons"]
        return data


# ==============================================================================
# PHASE 4: ACCOUNTS, PERSISTENCE & PERSONALIZATION SCHEMAS
# ==============================================================================

class RegisterRequest(BaseModel):
    """Account registration payload."""
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for forbidden in FORBIDDEN_PRIVACY_FIELDS:
                if forbidden in data and forbidden != "password":
                    raise ValueError(f"Privacy violation: field '{forbidden}' is forbidden.")
        return data


class LoginRequest(BaseModel):
    """Account authentication payload."""
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class StudentAccountItem(BaseModel):
    """Safe authenticated student account identity."""
    id: str
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    has_profile: bool = False

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Authentication outcome with session bearer token."""
    account: StudentAccountItem
    token: str
    expires_at: datetime


class PersistentProfileResponse(BaseModel):
    """Persistent student profile representation."""
    id: str
    account_id: Optional[str] = None
    citizenship_country: str
    residence_country: str
    intended_degree_level: str
    intended_destination_country: str
    gpa: Optional[float] = None
    gpa_scale: Optional[float] = 4.0
    intended_major: Optional[str] = None
    english_test_type: Optional[str] = None
    english_test_score: Optional[float] = None
    sat_score: Optional[int] = None
    act_score: Optional[int] = None
    financial_need_tier: Optional[str] = None
    academic_achievements: List[str] = Field(default_factory=list)
    extracurricular_activities: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersistentProfileUpdate(BaseModel):
    """Payload to update an authenticated student's persistent profile."""
    citizenship_country: Optional[str] = Field(None, min_length=2, max_length=3)
    residence_country: Optional[str] = Field(None, min_length=2, max_length=3)
    intended_degree_level: Optional[str] = Field("BACHELOR")
    intended_destination_country: Optional[str] = Field("US")
    gpa: Optional[float] = Field(None, ge=0.0, le=100.0)
    gpa_scale: Optional[float] = Field(4.0, ge=1.0, le=100.0)
    intended_major: Optional[str] = None
    english_test_type: Optional[str] = None
    english_test_score: Optional[float] = None
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    act_score: Optional[int] = Field(None, ge=1, le=36)
    financial_need_tier: Optional[str] = None
    academic_achievements: Optional[List[str]] = None
    extracurricular_activities: Optional[List[str]] = None
    interests: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_privacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for forbidden in FORBIDDEN_PRIVACY_FIELDS:
                if forbidden in data:
                    raise ValueError(f"Privacy violation: field '{forbidden}' is strictly forbidden.")
        return data


class SavedOpportunityItem(BaseModel):
    """Saved opportunity with current canonical intelligence."""
    id: str
    student_account_id: str
    opportunity_id: str
    saved_at: datetime
    opportunity: OpportunitySummary

    model_config = ConfigDict(from_attributes=True)


class PaginatedSavedOpportunities(BaseModel):
    """Pagination wrapper for saved scholarship list."""
    items: List[SavedOpportunityItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApplicationRecordCreate(BaseModel):
    """Payload to track a scholarship application."""
    opportunity_id: str = Field(..., min_length=1)
    status: str = Field("NOT_STARTED", description="ApplicationStatus enum")
    student_notes: Optional[str] = Field(None, max_length=5000)
    submitted_at: Optional[datetime] = None


class ApplicationRecordUpdate(BaseModel):
    """Payload to update an existing application record."""
    status: Optional[str] = None
    student_notes: Optional[str] = Field(None, max_length=5000)
    submitted_at: Optional[datetime] = None


class ApplicationRecordItem(BaseModel):
    """Application record item with current canonical intelligence."""
    id: str
    student_account_id: str
    opportunity_id: str
    status: str
    student_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    opportunity: OpportunitySummary

    model_config = ConfigDict(from_attributes=True)


class PaginatedApplications(BaseModel):
    """Pagination wrapper for application records."""
    items: List[ApplicationRecordItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ComparisonSelectionItem(BaseModel):
    """Persistent comparison selection item."""
    id: str
    opportunity_id: str
    created_at: datetime
    opportunity: OpportunitySummary

    model_config = ConfigDict(from_attributes=True)


class PersistentComparisonResponse(BaseModel):
    """Persistent comparison set for an authenticated student."""
    items: List[ComparisonSelectionItem]
    count: int
    max_allowed: int = 4

