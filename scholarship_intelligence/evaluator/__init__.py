"""Phase 1D Deterministic Eligibility Evaluation Engine package."""
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.evaluator.field_registry import is_field_allowed, resolve_field_name
from scholarship_intelligence.evaluator.logic import (
    evaluate_and,
    evaluate_and_all,
    evaluate_not,
    evaluate_or,
    evaluate_or_all,
)
from scholarship_intelligence.evaluator.operators import evaluate_comparison
from scholarship_intelligence.evaluator.validator import RuleValidationError, validate_rule_expression
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)

__all__ = [
    "EligibilityEvaluator",
    "EligibilityStatus",
    "RuleEvaluationResult",
    "EligibilityEvaluationResult",
    "RuleValidationError",
    "validate_rule_expression",
    "evaluate_and",
    "evaluate_and_all",
    "evaluate_or",
    "evaluate_or_all",
    "evaluate_not",
    "evaluate_comparison",
    "is_field_allowed",
    "resolve_field_name",
]
