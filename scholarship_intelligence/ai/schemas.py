"""Pydantic schemas and DTOs for the Phase 5 AI Counselor.

Guarantees:
- Strict separation between trusted structured intelligence and untrusted conversation input.
- Epistemic status tracking without arbitrary numerical or probabilistic scores.
- Traceable citations linking directly to official verified sources.
- Complete privacy protection (forbidden identity fields excluded from all context).
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import (
    AlignmentLevel,
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    ReadinessLevel,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


class EpistemicStatus(str, Enum):
    """Qualitative grounding state of the counselor response."""
    GROUNDED = "GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    CONFLICTING_INFORMATION = "CONFLICTING_INFORMATION"


class SourceCitation(BaseModel):
    """Institutional or provider source supporting guidance."""
    title: str = Field(..., description="Name or title of the source")
    url: Optional[str] = Field(None, description="Direct URL of the verified or discovery source")
    authority_tier: Optional[str] = Field(None, description="Authority hierarchy tier")
    verification_status: Optional[str] = Field(None, description="Verification state of facts from this source")
    evidence_quote: Optional[str] = Field(None, description="Concise quoted snippet from the source")
    is_primary: bool = Field(False, description="Whether this is the primary authoritative source")

    model_config = ConfigDict(from_attributes=True)


class CounselorContext(BaseModel):
    """Minimal, privacy-sanitized structured facts provided to the AI counselor."""
    opportunity_id: str
    opportunity_title: str
    provider_name: Optional[str] = None
    university_name: Optional[str] = None
    target_degree_level: str = "BACHELOR"
    destination_country: str = "US"
    academic_cycle: str = "2026-2027"
    verification_status: str = "UNVERIFIED"
    freshness_level: str = "UNVERIFIED"
    epistemic_status: EpistemicStatus = EpistemicStatus.GROUNDED
    funding_classification: str = "UNKNOWN"
    funding_summary: str = ""
    tuition_covered: str = "UNKNOWN"
    living_expenses_covered: str = "UNKNOWN"
    fees_covered: str = "UNKNOWN"
    deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    earliest_deadline: Optional[str] = None
    deadline_status: str = "UNKNOWN"
    eligibility_status: str = "NEEDS_INFORMATION"
    academic_alignment: str = "UNKNOWN"
    geographic_alignment: str = "UNKNOWN"
    program_alignment: str = "UNKNOWN"
    testing_readiness: str = "UNKNOWN"
    application_readiness: str = "UNKNOWN"
    student_profile_facts: Dict[str, Any] = Field(default_factory=dict)
    satisfied_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)
    unknown_rules: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    evidence_sources: List[SourceCitation] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    """Single turn in a bounded student-counselor conversation."""
    role: str = Field(..., pattern="^(user|assistant)$", description="Speaker role")
    content: str = Field(..., min_length=1, max_length=2000, description="Message text")


class AICounselorRequest(BaseModel):
    """Request payload for student inquiry to AI counselor."""
    opportunity_id: str = Field(..., description="UUID of the scholarship opportunity")
    message: str = Field(..., min_length=1, max_length=1000, description="Student question or prompt")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=6,
        description="Prior conversation turns for bounded dialogue context",
    )


class AICounselorResponse(BaseModel):
    """Structured, validated response returned to the student."""
    answer: str = Field(..., description="Natural language explanation grounded in verified facts")
    epistemic_status: EpistemicStatus = Field(..., description="Epistemic grounding level")
    warnings: List[str] = Field(default_factory=list, description="Verification or eligibility cautions")
    sources: List[SourceCitation] = Field(default_factory=list, description="Authoritative sources consulted")
    known_facts: List[str] = Field(default_factory=list, description="Key facts established with high authority")
    unknowns: List[str] = Field(default_factory=list, description="Unconfirmed criteria requiring student verification")
    next_steps: List[str] = Field(default_factory=list, description="Deterministic actionable steps")
    disclaimer: str = Field(
        default="AI guidance explains the verified scholarship information available in the system. It does not determine admission or scholarship selection outcomes. Always verify important requirements and deadlines with the official source.",
        description="Mandatory epistemic disclaimer",
    )
    is_fallback: bool = Field(False, description="True if response was produced by deterministic fallback engine")
