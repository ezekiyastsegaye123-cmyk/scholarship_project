"""Formal, bounded grammar for eligibility rule expressions.

Guarantees:
- Safe AST validation with strict Pydantic models.
- Maximum nesting depth of 5 levels.
- Zero dynamic code execution (no eval, no exec, no SQL fragments).
"""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleKind, RuleLogicalOp


MAX_RULE_DEPTH = 5


class ComparisonExpression(BaseModel):
    """Field-level comparison expression."""
    op: RuleComparisonOp
    field: str = Field(..., min_length=1, max_length=100)
    value: Any
    scale: Optional[float] = None

    @field_validator("field")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        # Prevent injection or suspicious field syntax
        allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_.")
        if not set(v.lower()).issubset(allowed_chars):
            raise ValueError(f"Invalid field name '{v}': must contain only alphanumeric characters, underscores, or periods")
        return v


class LogicalExpression(BaseModel):
    """Composite boolean logical expression with nesting depth bounds."""
    op: RuleLogicalOp
    operands: List[Union["LogicalExpression", ComparisonExpression]] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_logical_structure(self) -> "LogicalExpression":
        if self.op == RuleLogicalOp.NOT:
            if len(self.operands) != 1:
                raise ValueError("Logical operator 'NOT' must have exactly one operand")
        else:
            if len(self.operands) < 2:
                raise ValueError(f"Logical operator '{self.op.value}' must have at least two operands")
        
        # Validate depth
        depth = calculate_expression_depth(self)
        if depth > MAX_RULE_DEPTH:
            raise ValueError(f"Rule expression exceeds maximum allowed nesting depth of {MAX_RULE_DEPTH} (found depth {depth})")
        return self


def calculate_expression_depth(expr: Union[LogicalExpression, ComparisonExpression]) -> int:
    """Calculates recursive AST depth."""
    if isinstance(expr, ComparisonExpression):
        return 1
    if isinstance(expr, LogicalExpression):
        if not expr.operands:
            return 1
        return 1 + max(calculate_expression_depth(op) for op in expr.operands)
    return 1


RuleExpression = Union[LogicalExpression, ComparisonExpression]


class EligibilityRuleDefinition(BaseModel):
    """Canonical model for an eligibility rule with provenance linkage."""
    rule_id: str = Field(..., min_length=1, max_length=100)
    kind: RuleKind = RuleKind.REQUIRED
    expression: RuleExpression
    description: Optional[str] = None
    source_evidence_snippet: Optional[str] = None
