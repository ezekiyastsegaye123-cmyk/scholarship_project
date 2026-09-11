"""Strict AST validation for eligibility rules prior to evaluation.

Enforces:
- Bounded depth <= 5 (no DoS or infinite recursion).
- Allowed operators (RuleComparisonOp, RuleLogicalOp).
- Operand counts (NOT exactly 1; AND/OR >= 2).
- Strict field allowlist checking.
- Operator/field type compatibility.
- Zero arbitrary code execution or code fragments.
"""
from typing import Any, Union
from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleLogicalOp
from scholarship_intelligence.domain.rules import (
    ComparisonExpression,
    EligibilityRuleDefinition,
    LogicalExpression,
    MAX_RULE_DEPTH,
    RuleExpression,
    calculate_expression_depth,
)
from scholarship_intelligence.evaluator.field_registry import (
    get_field_metadata,
    is_field_allowed,
    resolve_field_name,
)


class RuleValidationError(ValueError):
    """Raised when an eligibility rule expression is malformed or invalid."""
    pass


def validate_rule_expression(expr: Any, current_depth: int = 1) -> None:
    """Validates an expression AST recursively.
    
    Raises:
        RuleValidationError on any violation.
    """
    if current_depth > MAX_RULE_DEPTH:
        raise RuleValidationError(f"Rule expression exceeds maximum allowed nesting depth of {MAX_RULE_DEPTH}")
    
    # 1. Handle dict representation
    if isinstance(expr, dict):
        op_raw = expr.get("op")
        if not op_raw:
            raise RuleValidationError("Rule expression missing required 'op' field")
        
        # Check if logical operator
        if str(op_raw).upper() in {o.value for o in RuleLogicalOp}:
            log_op = RuleLogicalOp(str(op_raw).upper())
            operands = expr.get("operands")
            if not isinstance(operands, list):
                raise RuleValidationError(f"Logical operator '{log_op.value}' requires a list of operands")
            if log_op == RuleLogicalOp.NOT:
                if len(operands) != 1:
                    raise RuleValidationError("Logical operator 'NOT' must have exactly 1 operand")
            else:
                if len(operands) < 2:
                    raise RuleValidationError(f"Logical operator '{log_op.value}' must have at least 2 operands")
            
            for child in operands:
                validate_rule_expression(child, current_depth=current_depth + 1)
            return

        # Check if comparison operator
        if str(op_raw).upper() in {o.value for o in RuleComparisonOp}:
            comp_op = RuleComparisonOp(str(op_raw).upper())
            raw_field = expr.get("field")
            if not raw_field or not isinstance(raw_field, str):
                raise RuleValidationError("Comparison expression requires a valid non-empty 'field' string")
            
            if not is_field_allowed(raw_field):
                raise RuleValidationError(f"Field '{raw_field}' is not in the registered field allowlist")
            
            if "value" not in expr:
                raise RuleValidationError(f"Comparison expression on field '{raw_field}' missing 'value'")
            
            value = expr.get("value")
            _validate_comp_op_compatibility(comp_op, raw_field, value)
            return

        raise RuleValidationError(f"Unknown rule operator '{op_raw}'")

    # 2. Handle Pydantic LogicalExpression
    if isinstance(expr, LogicalExpression):
        depth = calculate_expression_depth(expr)
        if depth > MAX_RULE_DEPTH:
            raise RuleValidationError(f"Rule expression exceeds maximum allowed nesting depth of {MAX_RULE_DEPTH}")
        for child in expr.operands:
            validate_rule_expression(child, current_depth=current_depth + 1)
        return

    # 3. Handle Pydantic ComparisonExpression
    if isinstance(expr, ComparisonExpression):
        if not is_field_allowed(expr.field):
            raise RuleValidationError(f"Field '{expr.field}' is not in the registered field allowlist")
        _validate_comp_op_compatibility(expr.op, expr.field, expr.value)
        return

    raise RuleValidationError(f"Invalid rule expression object type: {type(expr).__name__}")


def _validate_comp_op_compatibility(op: RuleComparisonOp, raw_field: str, value: Any) -> None:
    """Validate that operator and value are compatible with the registered field."""
    meta = get_field_metadata(raw_field)
    if not meta:
        raise RuleValidationError(f"Field '{raw_field}' not registered")
    
    if op not in meta.supported_ops:
        raise RuleValidationError(
            f"Operator '{op.value}' is not supported for field '{raw_field}' (supported: {[o.value for o in meta.supported_ops]})"
        )
    
    if op == RuleComparisonOp.IN:
        if not isinstance(value, (list, tuple, set)):
            raise RuleValidationError(f"Operator 'IN' requires collection value (list/tuple/set), got {type(value).__name__}")
        if not value:
            raise RuleValidationError("Operator 'IN' collection must not be empty")

    if op in (RuleComparisonOp.GT, RuleComparisonOp.GTE, RuleComparisonOp.LT, RuleComparisonOp.LTE):
        if not isinstance(value, (int, float)):
            raise RuleValidationError(f"Operator '{op.value}' requires numeric value, got {type(value).__name__}")
