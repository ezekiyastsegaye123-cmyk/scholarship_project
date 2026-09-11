"""Tests for rule AST grammar validation and safety checks."""
import pytest
from scholarship_intelligence.evaluator.validator import (
    RuleValidationError,
    validate_rule_expression,
)


def test_valid_expression_passes():
    valid_expr = {
        "op": "AND",
        "operands": [
            {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
            {"op": "IN", "field": "citizenship_country", "value": ["ETH", "KEN"]},
        ],
    }
    # Should not raise
    validate_rule_expression(valid_expr)


def test_depth_limit_enforcement():
    """Rules nested more than 5 levels deep must be rejected."""
    # Build 6-level deep expression
    deep_expr = {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0}
    for _ in range(5):
        deep_expr = {
            "op": "AND",
            "operands": [
                deep_expr,
                {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
            ],
        }

    with pytest.raises(RuleValidationError, match="maximum allowed nesting depth"):
        validate_rule_expression(deep_expr)


def test_invalid_operator_rejected():
    expr = {"op": "SQL_INJECTION", "field": "gpa", "value": 3.5}
    with pytest.raises(RuleValidationError, match="Unknown rule operator"):
        validate_rule_expression(expr)


def test_unregistered_field_rejected():
    expr = {"op": "EQ", "field": "bank_account_balance", "value": 10000}
    with pytest.raises(RuleValidationError, match="not in the registered field allowlist"):
        validate_rule_expression(expr)


def test_incompatible_operator_and_field():
    # CONTAINS on numeric float field
    expr = {"op": "CONTAINS", "field": "gpa", "value": "3.5"}
    with pytest.raises(RuleValidationError, match="is not supported for field"):
        validate_rule_expression(expr)


def test_logical_not_operand_count():
    # NOT with 2 operands must fail
    expr = {
        "op": "NOT",
        "operands": [
            {"op": "EQ", "field": "citizenship_country", "value": "US"},
            {"op": "EQ", "field": "citizenship_country", "value": "CA"},
        ],
    }
    with pytest.raises(RuleValidationError, match="must have exactly 1 operand"):
        validate_rule_expression(expr)


def test_logical_and_operand_count():
    # AND with only 1 operand must fail
    expr = {
        "op": "AND",
        "operands": [
            {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
        ],
    }
    with pytest.raises(RuleValidationError, match="must have at least 2 operands"):
        validate_rule_expression(expr)
