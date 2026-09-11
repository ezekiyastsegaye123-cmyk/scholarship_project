"""Scholarship Counselor Module.

Provides qualitative, explainable decision-support for scholarship opportunities.
"""
from scholarship_intelligence.counselor.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.schemas.counselor import (
    AcademicAlignmentContext,
    ApplicationReadinessContext,
    CounselorAssessmentResult,
    DeadlineAssessmentContext,
    DeadlineItemContext,
    EvidenceReference,
    FundingAssessmentContext,
    GeographicAlignmentContext,
    ProgramAlignmentContext,
    TestingReadinessContext,
    VerificationWarningContext,
)

__all__ = [
    "ScholarshipCounselorService",
    "AlignmentLevel",
    "ReadinessLevel",
    "DeadlineReadiness",
    "CounselorAssessmentResult",
    "AcademicAlignmentContext",
    "GeographicAlignmentContext",
    "ProgramAlignmentContext",
    "TestingReadinessContext",
    "FundingAssessmentContext",
    "ApplicationReadinessContext",
    "DeadlineAssessmentContext",
    "DeadlineItemContext",
    "VerificationWarningContext",
    "EvidenceReference",
]
