"""Tests for formal, bounded eligibility rule grammar."""
import pytest
from pydantic import ValidationError

from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleKind, RuleLogicalOp
from scholarship_intelligence.domain.rules import (
    ComparisonExpression,
    EligibilityRuleDefinition,
    LogicalExpression,
    MAX_RULE_DEPTH,
    calculate_expression_depth,
)


def test_comparison_operators():
    """Validates all supported comparison operators."""
    for op in RuleComparisonOp:
        expr = ComparisonExpression(op=op, field="gpa", value=3.5)
        assert expr.op == op
        assert expr.field == "gpa"
        assert expr.value == 3.5


def test_field_name_sanitization():
    """Rejects dangerous or SQL-like field names."""
    with pytest.raises(ValidationError):
        ComparisonExpression(op=RuleComparisonOp.EQ, field="gpa; DROP TABLE students;--", value=3.5)

    with pytest.raises(ValidationError):
        ComparisonExpression(op=RuleComparisonOp.EQ, field="student()", value=3.5)


def test_logical_and_or():
    """Validates composite AND / OR logical expressions."""
    c1 = ComparisonExpression(op=RuleComparisonOp.GTE, field="gpa", value=3.5)
    c2 = ComparisonExpression(op=RuleComparisonOp.IN, field="class_rank", value=["top_10_percent"])

    or_expr = LogicalExpression(op=RuleLogicalOp.OR, operands=[c1, c2])
    assert or_expr.op == RuleLogicalOp.OR
    assert len(or_expr.operands) == 2
    assert calculate_expression_depth(or_expr) == 2

    and_expr = LogicalExpression(op=RuleLogicalOp.AND, operands=[c1, or_expr])
    assert and_expr.op == RuleLogicalOp.AND
    assert calculate_expression_depth(and_expr) == 3


def test_logical_not():
    """Validates unary NOT operator."""
    c1 = ComparisonExpression(op=RuleComparisonOp.EQ, field="is_us_citizen", value=True)
    not_expr = LogicalExpression(op=RuleLogicalOp.NOT, operands=[c1])
    assert not_expr.op == RuleLogicalOp.NOT
    assert len(not_expr.operands) == 1

    # NOT with more than 1 operand must fail
    c2 = ComparisonExpression(op=RuleComparisonOp.EQ, field="is_permanent_resident", value=True)
    with pytest.raises(ValidationError, match="exactly one operand"):
        LogicalExpression(op=RuleLogicalOp.NOT, operands=[c1, c2])


def test_nesting_depth_boundary():
    """Tests that nesting depth is strictly enforced to <= 5 levels."""
    # Build a depth-5 tree
    leaf = ComparisonExpression(op=RuleComparisonOp.EQ, field="level", value=1)
    l4 = LogicalExpression(op=RuleLogicalOp.NOT, operands=[leaf])
    l3 = LogicalExpression(op=RuleLogicalOp.NOT, operands=[l4])
    l2 = LogicalExpression(op=RuleLogicalOp.NOT, operands=[l3])
    l1 = LogicalExpression(op=RuleLogicalOp.NOT, operands=[l2])
    
    assert calculate_expression_depth(l1) == 5
    
    # Building depth 6 must raise ValidationError
    with pytest.raises(ValidationError, match="exceeds maximum allowed nesting depth of 5"):
        LogicalExpression(op=RuleLogicalOp.NOT, operands=[l1])


def test_eligibility_rule_definition_serialization():
    """Tests parsing a full structured JSON eligibility rule."""
    payload = {
        "rule_id": "rule_gpa_or_rank",
        "kind": "REQUIRED",
        "expression": {
            "op": "OR",
            "operands": [
                {"op": "GTE", "field": "gpa", "value": 3.8, "scale": 4.0},
                {"op": "IN", "field": "class_rank", "value": ["top_5_percent", "top_10_percent"]}
            ]
        },
        "description": "Requires minimum 3.8 GPA or top 10% class rank",
        "source_evidence_snippet": "Applicants must demonstrate academic excellence (3.8+ GPA or top 10%)."
    }
    rule = EligibilityRuleDefinition.model_validate(payload)
    assert rule.rule_id == "rule_gpa_or_rank"
    assert rule.kind == RuleKind.REQUIRED
    assert isinstance(rule.expression, LogicalExpression)
    assert len(rule.expression.operands) == 2
