"""Phase 1C Verification, Provenance, Liveness, and Conflict Resolution Layer."""
from scholarship_intelligence.verification.authority import (
    AuthorityClassifier,
    classify_url_authority,
    compare_authority,
    get_authority_rank,
)
from scholarship_intelligence.verification.conflict import ConflictEngine, ConflictResolutionOutcome
from scholarship_intelligence.verification.content_comparator import ContentComparator, ContentComparisonResult
from scholarship_intelligence.verification.engine import VerificationEngine
from scholarship_intelligence.verification.fact_verifier import FactVerifier
from scholarship_intelligence.verification.liveness import SourceLivenessChecker
from scholarship_intelligence.verification.promoter import CanonicalPromoter
from scholarship_intelligence.verification.risk_triage import RiskTriager, RiskTriageResult

__all__ = [
    "AuthorityClassifier",
    "classify_url_authority",
    "compare_authority",
    "get_authority_rank",
    "ConflictEngine",
    "ConflictResolutionOutcome",
    "ContentComparator",
    "ContentComparisonResult",
    "VerificationEngine",
    "FactVerifier",
    "SourceLivenessChecker",
    "CanonicalPromoter",
    "RiskTriager",
    "RiskTriageResult",
]
