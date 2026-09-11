"""Type-safe comparison and membership operators for deterministic eligibility evaluation.

Guarantees:
- Safe numeric and scale-aware comparisons.
- Zero unsafe Python eval/exec.
- Returns TriState outcomes.
- If student value is None or missing, returns TriState.UNKNOWN (never NO).
- Scale mismatch without conversion returns TriState.UNKNOWN.
"""
from typing import Any, Iterable, Optional, Sequence, Union
from scholarship_intelligence.domain.enums import RuleComparisonOp, TriState


# Common country aliases (ISO-2, ISO-3, common name)
COUNTRY_ALIASES: dict[str, set[str]] = {
    "et": {"et", "eth", "ethiopia"},
    "eth": {"et", "eth", "ethiopia"},
    "ethiopia": {"et", "eth", "ethiopia"},
    "ke": {"ke", "ken", "kenya"},
    "ken": {"ke", "ken", "kenya"},
    "kenya": {"ke", "ken", "kenya"},
    "ng": {"ng", "nga", "nigeria"},
    "nga": {"ng", "nga", "nigeria"},
    "nigeria": {"ng", "nga", "nigeria"},
    "ug": {"ug", "uga", "uganda"},
    "uga": {"ug", "uga", "uganda"},
    "uganda": {"ug", "uga", "uganda"},
    "rw": {"rw", "rwa", "rwanda"},
    "rwa": {"rw", "rwa", "rwanda"},
    "rwanda": {"rw", "rwa", "rwanda"},
    "gh": {"gh", "gha", "ghana"},
    "gha": {"gh", "gha", "ghana"},
    "ghana": {"gh", "gha", "ghana"},
    "us": {"us", "usa", "united states", "united states of america"},
    "usa": {"us", "usa", "united states", "united states of america"},
    "united states": {"us", "usa", "united states", "united states of america"},
}


def _normalize_string(val: Any) -> str:
    """Normalize string by trimming and lowercasing."""
    if val is None:
        return ""
    return str(val).strip().lower()


def _country_matches(student_val: str, expected_val: str) -> bool:
    """Check if two country identifiers match, considering common codes/names."""
    norm_s = _normalize_string(student_val)
    norm_e = _normalize_string(expected_val)
    if norm_s == norm_e:
        return True
    
    # Check alias sets
    s_aliases = COUNTRY_ALIASES.get(norm_s)
    if s_aliases and norm_e in s_aliases:
        return True
    e_aliases = COUNTRY_ALIASES.get(norm_e)
    if e_aliases and norm_s in e_aliases:
        return True
    return False


def _is_country_in_collection(student_val: str, collection: Iterable[Any]) -> bool:
    """Check if student country matches any item in collection."""
    for item in collection:
        if _country_matches(student_val, str(item)):
            return True
    return False


def evaluate_comparison(
    op: RuleComparisonOp,
    field: str,
    expected_value: Any,
    actual_value: Any,
    expected_scale: Optional[float] = None,
    student_scale: Optional[float] = None,
) -> tuple[TriState, str]:
    """Evaluates a comparison operator between expected rule value and actual student profile value.
    
    Returns:
        (TriState, reason_description)
    """
    # 1. Missing student value -> UNKNOWN
    if actual_value is None:
        return TriState.UNKNOWN, f"Student profile is missing required value for field '{field}'"
    
    # 2. GPA scale handling
    if "gpa" in field.lower():
        return _evaluate_gpa(op, expected_value, actual_value, expected_scale, student_scale)
    
    # 3. Membership operator: IN
    if op == RuleComparisonOp.IN:
        return _evaluate_in(field, expected_value, actual_value)
    
    # 4. Containment operator: CONTAINS
    if op == RuleComparisonOp.CONTAINS:
        return _evaluate_contains(field, expected_value, actual_value)
    
    # 5. Equality / Inequality
    if op in (RuleComparisonOp.EQ, RuleComparisonOp.NEQ):
        return _evaluate_equality(op, field, expected_value, actual_value)
    
    # 6. Ordered numeric / comparable operations (GT, GTE, LT, LTE)
    if op in (RuleComparisonOp.GT, RuleComparisonOp.GTE, RuleComparisonOp.LT, RuleComparisonOp.LTE):
        return _evaluate_ordered(op, field, expected_value, actual_value)
    
    return TriState.UNKNOWN, f"Unsupported comparison operator '{op.value}'"


def _evaluate_gpa(
    op: RuleComparisonOp,
    expected_value: Any,
    actual_value: Any,
    expected_scale: Optional[float],
    student_scale: Optional[float],
) -> tuple[TriState, str]:
    """Scale-aware GPA evaluation."""
    try:
        exp_val = float(expected_value)
        act_val = float(actual_value)
    except (ValueError, TypeError):
        return TriState.UNKNOWN, f"Cannot parse GPA values for comparison: expected={expected_value}, actual={actual_value}"
    
    # Default scale is 4.0 if not explicitly defined
    e_scale = float(expected_scale) if expected_scale is not None else 4.0
    s_scale = float(student_scale) if student_scale is not None else 4.0
    
    if e_scale != s_scale:
        return (
            TriState.UNKNOWN,
            f"GPA scale mismatch (required scale {e_scale}, student scale {s_scale}). "
            f"No conversion rule defined; cannot infer eligibility."
        )
    
    # Compare with matching scale
    matched = _compare_numeric(op, act_val, exp_val)
    if matched is None:
        return TriState.UNKNOWN, f"Invalid GPA comparison operator '{op.value}'"
    
    if matched:
        return TriState.YES, f"GPA {act_val:.2f} satisfies {op.value} {exp_val:.2f} on {e_scale:.1f} scale"
    else:
        return TriState.NO, f"GPA {act_val:.2f} does not satisfy {op.value} {exp_val:.2f} on {e_scale:.1f} scale"


def _evaluate_in(
    field: str,
    expected_collection: Any,
    actual_value: Any,
) -> tuple[TriState, str]:
    """Evaluates whether actual_value is in expected_collection."""
    if not isinstance(expected_collection, (list, tuple, set)):
        return TriState.UNKNOWN, f"Expected value for 'IN' operator must be a collection, got {type(expected_collection).__name__}"
    
    # Country-aware matching
    if any(k in field.lower() for k in ("country", "citizenship", "residence", "nationality")):
        if _is_country_in_collection(str(actual_value), expected_collection):
            return TriState.YES, f"{field} '{actual_value}' is in allowed list"
        return TriState.NO, f"{field} '{actual_value}' is not in allowed list {list(expected_collection)}"
    
    # Standard collection matching
    norm_actual = _normalize_string(actual_value)
    norm_collection = [_normalize_string(item) for item in expected_collection]
    
    if norm_actual in norm_collection:
        return TriState.YES, f"{field} '{actual_value}' is in allowed values"
    return TriState.NO, f"{field} '{actual_value}' is not in allowed values"


def _evaluate_contains(
    field: str,
    expected_value: Any,
    actual_value: Any,
) -> tuple[TriState, str]:
    """Evaluates whether actual_value contains expected_value."""
    norm_expected = _normalize_string(expected_value)
    
    # If student value is a list/set of items (e.g. interests, extracurriculars)
    if isinstance(actual_value, (list, tuple, set)):
        for item in actual_value:
            if norm_expected in _normalize_string(item):
                return TriState.YES, f"{field} contains '{expected_value}'"
        return TriState.NO, f"{field} does not contain '{expected_value}'"
    
    # If student value is a string
    if isinstance(actual_value, str):
        if norm_expected in _normalize_string(actual_value):
            return TriState.YES, f"{field} contains '{expected_value}'"
        return TriState.NO, f"{field} does not contain '{expected_value}'"
    
    return TriState.UNKNOWN, f"Field '{field}' type {type(actual_value).__name__} does not support CONTAINS operator"


def _evaluate_equality(
    op: RuleComparisonOp,
    field: str,
    expected_value: Any,
    actual_value: Any,
) -> tuple[TriState, str]:
    """Evaluates EQ / NEQ."""
    # Country field special handling
    if any(k in field.lower() for k in ("country", "citizenship", "residence", "nationality")):
        matches = _country_matches(str(actual_value), str(expected_value))
    elif isinstance(actual_value, str) and isinstance(expected_value, str):
        matches = _normalize_string(actual_value) == _normalize_string(expected_value)
    elif isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
        matches = float(actual_value) == float(expected_value)
    elif isinstance(actual_value, bool) or isinstance(expected_value, bool):
        matches = bool(actual_value) == bool(expected_value)
    else:
        matches = str(actual_value).strip() == str(expected_value).strip()
    
    if op == RuleComparisonOp.EQ:
        if matches:
            return TriState.YES, f"{field} '{actual_value}' equals expected '{expected_value}'"
        return TriState.NO, f"{field} '{actual_value}' does not equal expected '{expected_value}'"
    else:  # NEQ
        if not matches:
            return TriState.YES, f"{field} '{actual_value}' does not equal restricted '{expected_value}'"
        return TriState.NO, f"{field} '{actual_value}' equals restricted '{expected_value}'"


def _evaluate_ordered(
    op: RuleComparisonOp,
    field: str,
    expected_value: Any,
    actual_value: Any,
) -> tuple[TriState, str]:
    """Evaluates ordered numeric comparisons (GT, GTE, LT, LTE)."""
    try:
        act_num = float(actual_value)
        exp_num = float(expected_value)
    except (ValueError, TypeError):
        return TriState.UNKNOWN, f"Cannot perform numeric comparison on non-numeric types for field '{field}': expected={expected_value}, actual={actual_value}"
    
    matched = _compare_numeric(op, act_num, exp_num)
    if matched is None:
        return TriState.UNKNOWN, f"Invalid comparison operator '{op.value}'"
    
    if matched:
        return TriState.YES, f"{field} ({act_num}) satisfies {op.value} {exp_num}"
    else:
        return TriState.NO, f"{field} ({act_num}) does not satisfy {op.value} {exp_num}"


def _compare_numeric(op: RuleComparisonOp, actual: float, expected: float) -> Optional[bool]:
    """Raw numeric comparison helper."""
    if op == RuleComparisonOp.GT:
        return actual > expected
    if op == RuleComparisonOp.GTE:
        return actual >= expected
    if op == RuleComparisonOp.LT:
        return actual < expected
    if op == RuleComparisonOp.LTE:
        return actual <= expected
    if op == RuleComparisonOp.EQ:
        return actual == expected
    if op == RuleComparisonOp.NEQ:
        return actual != expected
    return None
