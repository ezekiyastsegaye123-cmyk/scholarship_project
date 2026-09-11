"""Tests for handling conflicting profile data and conflict propagation."""
import pytest
from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleKind, TriState
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


def test_explicit_conflicted_field_flag():
    evaluator = EligibilityEvaluator()
    profile = {
        "citizenship_country": "ETH",
        "_conflicts": ["citizenship_country"],
    }

    rule = {
        "rule_id": "r_country",
        "kind": "REQUIRED",
        "expression": {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
    }

    res = evaluator.evaluate_rule(rule, profile)
    assert res.status == TriState.CONFLICTING
    assert "conflicting" in res.explanation.lower()


def test_implicit_conflicted_scalar_field():
    evaluator = EligibilityEvaluator()
    # Scalar field containing multiple contradictory values
    profile = {
        "citizenship_country": ["ETH", "KEN"],
    }

    rule = {
        "rule_id": "r_country",
        "kind": "REQUIRED",
        "expression": {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
    }

    res = evaluator.evaluate_rule(rule, profile)
    assert res.status == TriState.CONFLICTING


def test_conflict_aggregates_to_needs_review():
    evaluator = EligibilityEvaluator()
    profile = {
        "gpa": 3.9,
        "citizenship_country": "ETH",
        "_conflicts": ["citizenship_country"],
    }

    rules = [
        {
            "rule_id": "r1",
            "kind": "REQUIRED",
            "expression": {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
        },
        {
            "rule_id": "r2",
            "kind": "REQUIRED",
            "expression": {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
        },
    ]

    result = evaluator.evaluate_rules(rules, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert len(result.conflicting_rules) == 1
    assert len(result.satisfied_rules) == 1
    assert len(result.failed_rules) == 0
