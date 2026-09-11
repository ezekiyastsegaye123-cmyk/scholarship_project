"""Domain enums defining multi-state semantics, authority tiers, and classification models."""
from enum import Enum


class TriState(str, Enum):
    """Tri-State & Multi-State semantic representation.
    
    Critical rule: Missing information must NOT become FALSE.
    UNKNOWN is distinct from NO and NOT_APPLICABLE.
    """
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING = "CONFLICTING"


class AuthorityTier(str, Enum):
    """Source authority tiers establishing provenance hierarchy."""
    OFFICIAL_PROVIDER = "OFFICIAL_PROVIDER"
    OFFICIAL_UNIVERSITY = "OFFICIAL_UNIVERSITY"
    GOVERNMENT = "GOVERNMENT"
    DISCOVERY_AGGREGATOR = "DISCOVERY_AGGREGATOR"
    THIRD_PARTY = "THIRD_PARTY"


class VerificationState(str, Enum):
    """Explicit evidence-based verification states.
    
    QUARANTINED_FOR_REVIEW indicates a material risk or unresolved concern 
    requiring human review before it can be presented as trusted.
    No arbitrary numerical trust score or blunt auto-kill is permitted.
    """
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONFLICTING = "CONFLICTING"
    OUTDATED = "OUTDATED"
    UNVERIFIED = "UNVERIFIED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    QUARANTINED_FOR_REVIEW = "QUARANTINED_FOR_REVIEW"


class FundingClassification(str, Enum):
    """Overall funding coverage classification."""
    FULL_FUNDING = "FULL_FUNDING"
    FULL_TUITION = "FULL_TUITION"
    PARTIAL_FUNDING = "PARTIAL_FUNDING"
    STIPEND_ONLY = "STIPEND_ONLY"
    FEES_ONLY = "FEES_ONLY"
    UNKNOWN = "UNKNOWN"


class FundingComponentType(str, Enum):
    """Decomposed individual funding components."""
    TUITION = "TUITION"
    MANDATORY_FEES = "MANDATORY_FEES"
    ROOM = "ROOM"
    MEALS = "MEALS"
    HEALTH_INSURANCE = "HEALTH_INSURANCE"
    BOOKS = "BOOKS"
    TRAVEL = "TRAVEL"
    VISA_SUPPORT = "VISA_SUPPORT"
    LIVING_EXPENSES = "LIVING_EXPENSES"
    STIPEND = "STIPEND"
    OTHER = "OTHER"


class AmountPeriod(str, Enum):
    """Time periodicity for monetary funding amounts."""
    ANNUAL = "ANNUAL"
    TOTAL = "TOTAL"
    ONE_TIME = "ONE_TIME"
    UNKNOWN = "UNKNOWN"


class DeadlineType(str, Enum):
    """Distinct application and financial aid deadline categories."""
    SCHOLARSHIP_APPLICATION = "SCHOLARSHIP_APPLICATION"
    UNIVERSITY_APPLICATION = "UNIVERSITY_APPLICATION"
    FINANCIAL_AID = "FINANCIAL_AID"
    EARLY_ACTION = "EARLY_ACTION"
    EARLY_DECISION = "EARLY_DECISION"
    REGULAR_DECISION = "REGULAR_DECISION"
    PRIORITY = "PRIORITY"
    ROLLING = "ROLLING"
    NOMINATION = "NOMINATION"
    DOCUMENT_SUBMISSION = "DOCUMENT_SUBMISSION"
    INTERNATIONAL_STUDENT = "INTERNATIONAL_STUDENT"


class RuleKind(str, Enum):
    """Classification of eligibility rule constraint enforcement."""
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    PREFERRED = "PREFERRED"
    UNKNOWN = "UNKNOWN"


class RuleLogicalOp(str, Enum):
    """Allowed boolean logical operators for composite eligibility expressions."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class RuleComparisonOp(str, Enum):
    """Allowed comparison operators for field-level eligibility evaluations."""
    EQ = "EQ"
    NEQ = "NEQ"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    IN = "IN"
    CONTAINS = "CONTAINS"


class RequirementKind(str, Enum):
    """Enforcement level of an application requirement."""
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    PREFERRED = "PREFERRED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RequirementType(str, Enum):
    """Type of document, credential, or form required for application."""
    TRANSCRIPT = "TRANSCRIPT"
    RECOMMENDATION = "RECOMMENDATION"
    ESSAY = "ESSAY"
    STANDARDIZED_TEST = "STANDARDIZED_TEST"
    ENGLISH_PROFICIENCY = "ENGLISH_PROFICIENCY"
    CSS_PROFILE = "CSS_PROFILE"
    ISFAA = "ISFAA"
    FINANCIAL_DOCUMENTS = "FINANCIAL_DOCUMENTS"
    PORTFOLIO = "PORTFOLIO"
    APPLICATION_FORM = "APPLICATION_FORM"
    INTERVIEW = "INTERVIEW"
    OTHER = "OTHER"


class ConflictStatus(str, Enum):
    """Resolution status for conflicting evidence records."""
    OPEN = "OPEN"
    RESOLVED_OFFICIAL_PREFERRED = "RESOLVED_OFFICIAL_PREFERRED"
    RESOLVED_RECENCY_PREFERRED = "RESOLVED_RECENCY_PREFERRED"
    DISMISSED = "DISMISSED"


class LivenessStatus(str, Enum):
    """Source URL liveness and accessibility states."""
    LIVE = "LIVE"
    REDIRECTED = "REDIRECTED"
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_CONTENT = "INVALID_CONTENT"


class QuarantineReason(str, Enum):
    """Structured rationale for placing opportunity in QUARANTINED_FOR_REVIEW."""
    UNSUPPORTED_MATERIAL_CLAIM = "UNSUPPORTED_MATERIAL_CLAIM"
    SOURCE_IDENTITY_UNCLEAR = "SOURCE_IDENTITY_UNCLEAR"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"
    SUSPICIOUS_PAYMENT_REQUEST = "SUSPICIOUS_PAYMENT_REQUEST"
    PHISHING_INDICATOR = "PHISHING_INDICATOR"
    BROKEN_PROVENANCE = "BROKEN_PROVENANCE"
    OTHER = "OTHER"


class NeedPolicy(str, Enum):
    """Institutional admissions financial need policy for international undergraduates."""
    NEED_BLIND_INTERNATIONAL = "NEED_BLIND_INTERNATIONAL"
    NEED_AWARE_INTERNATIONAL = "NEED_AWARE_INTERNATIONAL"
    NO_AID_INTERNATIONAL = "NO_AID_INTERNATIONAL"
    UNKNOWN = "UNKNOWN"


class AlignmentLevel(str, Enum):
    """Qualitative assessment of student alignment with published criteria.
    
    Meanings:
    - STRONG: Clear alignment based on verified evidence.
    - MODERATE: Some alignment, but minor gaps or partial data exist.
    - LIMITED: Meaningful gaps relative to published criteria.
    - UNKNOWN: Insufficient verified information to assess.
    - NOT_ASSESSABLE: Criterion cannot responsibly be assessed from available data.
    """
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    LIMITED = "LIMITED"
    UNKNOWN = "UNKNOWN"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class ReadinessLevel(str, Enum):
    """Qualitative application preparation status.
    
    NOT a prediction of admission or award success.
    """
    READY = "READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    NEEDS_PREPARATION = "NEEDS_PREPARATION"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DeadlineReadiness(str, Enum):
    """Status of application and financial aid deadlines relative to evaluation date."""
    OPEN = "OPEN"
    CLOSING_SOON = "CLOSING_SOON"  # Within 14 days
    UPCOMING = "UPCOMING"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"
