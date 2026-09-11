"""Export all SQLAlchemy models and register them with declarative Base."""
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid
from scholarship_intelligence.models.provider import Provider
from scholarship_intelligence.models.university import University
from scholarship_intelligence.models.source import OfficialSource, DiscoverySource
from scholarship_intelligence.models.eligibility import EligibilityRule, Requirement
from scholarship_intelligence.models.funding import Award, FundingComponent
from scholarship_intelligence.models.deadline import Deadline
from scholarship_intelligence.models.verification import VerificationRecord
from scholarship_intelligence.models.conflict import ConflictRecord
from scholarship_intelligence.models.application_requirement import ApplicationRequirement
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.student_profile import StudentProfile
from scholarship_intelligence.models.verification_history import VerificationHistory
from scholarship_intelligence.models.source_liveness import SourceLivenessLog

__all__ = [
    "Base",
    "TimestampMixin",
    "generate_uuid",
    "Provider",
    "University",
    "OfficialSource",
    "DiscoverySource",
    "EligibilityRule",
    "Requirement",
    "Award",
    "FundingComponent",
    "Deadline",
    "VerificationRecord",
    "ConflictRecord",
    "ApplicationRequirement",
    "ScholarshipOpportunity",
    "StudentProfile",
    "VerificationHistory",
    "SourceLivenessLog",
]

