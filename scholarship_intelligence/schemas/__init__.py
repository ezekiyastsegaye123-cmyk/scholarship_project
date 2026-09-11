"""Export all canonical Pydantic schemas."""
from scholarship_intelligence.schemas.provider import ProviderBase, ProviderCreate, ProviderRead
from scholarship_intelligence.schemas.university import UniversityBase, UniversityCreate, UniversityRead
from scholarship_intelligence.schemas.source import (
    OfficialSourceBase,
    OfficialSourceCreate,
    OfficialSourceRead,
    DiscoverySourceBase,
    DiscoverySourceCreate,
    DiscoverySourceRead,
)
from scholarship_intelligence.schemas.eligibility import (
    EligibilityRuleBase,
    EligibilityRuleCreate,
    EligibilityRuleRead,
    RequirementBase,
    RequirementCreate,
    RequirementRead,
)
from scholarship_intelligence.schemas.funding import (
    AwardBase,
    AwardCreate,
    AwardRead,
    FundingComponentBase,
    FundingComponentCreate,
    FundingComponentRead,
)
from scholarship_intelligence.schemas.deadline import DeadlineBase, DeadlineCreate, DeadlineRead
from scholarship_intelligence.schemas.verification import (
    VerificationRecordBase,
    VerificationRecordCreate,
    VerificationRecordRead,
    ConflictRecordBase,
    ConflictRecordCreate,
    ConflictRecordRead,
)
from scholarship_intelligence.schemas.application_requirement import (
    ApplicationRequirementBase,
    ApplicationRequirementCreate,
    ApplicationRequirementRead,
)
from scholarship_intelligence.schemas.opportunity import (
    ScholarshipOpportunityBase,
    ScholarshipOpportunityCreate,
    ScholarshipOpportunityRead,
)
from scholarship_intelligence.schemas.student_profile import (
    StudentProfileBase,
    StudentProfileCreate,
    StudentProfileRead,
)

from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)

from scholarship_intelligence.schemas.counselor import (
    CounselorAssessmentResult,
)

__all__ = [
    "ProviderBase", "ProviderCreate", "ProviderRead",
    "UniversityBase", "UniversityCreate", "UniversityRead",
    "OfficialSourceBase", "OfficialSourceCreate", "OfficialSourceRead",
    "DiscoverySourceBase", "DiscoverySourceCreate", "DiscoverySourceRead",
    "EligibilityRuleBase", "EligibilityRuleCreate", "EligibilityRuleRead",
    "RequirementBase", "RequirementCreate", "RequirementRead",
    "AwardBase", "AwardCreate", "AwardRead",
    "FundingComponentBase", "FundingComponentCreate", "FundingComponentRead",
    "DeadlineBase", "DeadlineCreate", "DeadlineRead",
    "VerificationRecordBase", "VerificationRecordCreate", "VerificationRecordRead",
    "ConflictRecordBase", "ConflictRecordCreate", "ConflictRecordRead",
    "ApplicationRequirementBase", "ApplicationRequirementCreate", "ApplicationRequirementRead",
    "ScholarshipOpportunityBase", "ScholarshipOpportunityCreate", "ScholarshipOpportunityRead",
    "StudentProfileBase", "StudentProfileCreate", "StudentProfileRead",
    "EligibilityStatus", "RuleEvaluationResult", "EligibilityEvaluationResult",
    "CounselorAssessmentResult",
]
