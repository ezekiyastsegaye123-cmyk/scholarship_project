"""Pydantic schemas for qualitative counselor assessments.

Guarantees:
- Strict qualitative classifications without numerical scores or probabilities.
- Multi-dimensional decomposition: Eligibility, Academic, Geographic, Program, Testing, Funding, Readiness, Deadlines.
- Source-aware evidence provenance tracking.
"""
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import (
    AlignmentLevel,
    AuthorityTier,
    DeadlineReadiness,
    DeadlineType,
    FundingClassification,
    ReadinessLevel,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


class EvidenceReference(BaseModel):
    """Traceable provenance link to an official or discovery source."""
    topic: str = Field(..., description="Subject matter (e.g. 'Academic Requirement', 'Tuition Funding')")
    source_url: Optional[str] = Field(None, description="URL where evidence was cited")
    source_authority: Optional[AuthorityTier] = Field(None, description="Authority classification of the source")
    evidence_quote: Optional[str] = Field(None, description="Direct quote or snippet from the source")

    model_config = ConfigDict(from_attributes=True)


class AcademicAlignmentContext(BaseModel):
    """Qualitative assessment of academic alignment."""
    level: AlignmentLevel
    student_gpa: Optional[float] = None
    student_scale: Optional[float] = None
    required_gpa: Optional[float] = None
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GeographicAlignmentContext(BaseModel):
    """Qualitative assessment of citizenship and residence criteria."""
    level: AlignmentLevel
    citizenship_country: Optional[str] = None
    residence_country: Optional[str] = None
    eligible_countries: List[str] = Field(default_factory=list)
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProgramAlignmentContext(BaseModel):
    """Qualitative assessment of field of study / major alignment."""
    level: AlignmentLevel
    declared_major: Optional[str] = None
    eligible_programs: List[str] = Field(default_factory=list)
    has_major_restriction: bool = False
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TestingReadinessContext(BaseModel):
    """Qualitative assessment of testing preparedness."""
    level: ReadinessLevel
    requires_sat: TriState = TriState.UNKNOWN
    requires_act: TriState = TriState.UNKNOWN
    student_sat: Optional[int] = None
    student_act: Optional[int] = None
    student_english_score: Optional[float] = None
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FundingAssessmentContext(BaseModel):
    """Decomposed qualitative assessment of funding coverage."""
    funding_classification: FundingClassification
    tuition_covered: TriState = TriState.UNKNOWN
    living_expenses_covered: TriState = TriState.UNKNOWN
    fees_covered: TriState = TriState.UNKNOWN
    books_covered: TriState = TriState.UNKNOWN
    travel_covered: TriState = TriState.UNKNOWN
    health_insurance_covered: TriState = TriState.UNKNOWN
    stipend_covered: TriState = TriState.UNKNOWN
    is_renewable: TriState = TriState.UNKNOWN
    estimated_annual_value_usd: Optional[float] = None
    summary: str
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApplicationReadinessContext(BaseModel):
    """Qualitative assessment of application preparation components."""
    level: ReadinessLevel
    total_requirements_count: int = 0
    required_components: List[str] = Field(default_factory=list)
    optional_components: List[str] = Field(default_factory=list)
    missing_components: List[str] = Field(default_factory=list)
    details: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DeadlineItemContext(BaseModel):
    """Single application or financial aid deadline evaluation."""
    deadline_type: DeadlineType
    deadline_date: Optional[date] = None
    readiness: DeadlineReadiness
    days_remaining: Optional[int] = None
    is_exact_date: bool = True
    timezone: Optional[str] = "America/New_York"
    context_description: Optional[str] = None
    evidence_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeadlineAssessmentContext(BaseModel):
    """Overall assessment across all published deadlines."""
    deadlines: List[DeadlineItemContext] = Field(default_factory=list)
    has_passed_deadline: bool = False
    earliest_upcoming_deadline: Optional[DeadlineItemContext] = None
    summary: str

    model_config = ConfigDict(from_attributes=True)


class VerificationWarningContext(BaseModel):
    """Transparency context for opportunity verification state."""
    verification_status: VerificationState
    evaluation_contains_unverified_facts: bool = False
    has_warning: bool = False
    warning_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CounselorAssessmentResult(BaseModel):
    """Canonical qualitative counselor decision-support output."""
    opportunity_id: Optional[str] = None
    opportunity_title: str
    student_id: Optional[str] = None
    eligibility_status: EligibilityStatus
    eligibility_summary: str
    academic_alignment: AcademicAlignmentContext
    geographic_alignment: GeographicAlignmentContext
    program_alignment: ProgramAlignmentContext
    testing_readiness: TestingReadinessContext
    funding_assessment: FundingAssessmentContext
    application_readiness: ApplicationReadinessContext
    deadline_assessment: DeadlineAssessmentContext
    verification_context: VerificationWarningContext
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
