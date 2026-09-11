"""Tests verifying strict preservation of UNKNOWN semantics.

Core Axioms:
- UNKNOWN != NO
- Missing student profile information MUST yield UNKNOWN, never NO or INELIGIBLE.
- NOT UNKNOWN == UNKNOWN (negating unknown never creates truth).
"""
import pytest
from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleKind, TriState
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


def test_missing_profile_fields_yield_unknown():
    evaluator = EligibilityEvaluator()
    empty_profile = {}

    rule_gpa = {
        "rule_id": "r_gpa",
        "kind": "REQUIRED",
        "expression": {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
    }
    rule_sat = {
        "rule_id": "r_sat",
        "kind": "REQUIRED",
        "expression": {"op": "GTE", "field": "sat_score", "value": 1400},
    }
    rule_citizenship = {
        "rule_id": "r_country",
        "kind": "REQUIRED",
        "expression": {"op": "IN", "field": "citizenship_country", "value": ["ETH", "KEN"]},
    }

    res_gpa = evaluator.evaluate_rule(rule_gpa, empty_profile)
    assert res_gpa.status == TriState.UNKNOWN
    assert "not been provided" in res_gpa.explanation

    res_sat = evaluator.evaluate_rule(rule_sat, empty_profile)
    assert res_sat.status == TriState.UNKNOWN

    res_country = evaluator.evaluate_rule(rule_citizenship, empty_profile)
    assert res_country.status == TriState.UNKNOWN


def test_negating_unknown_remains_unknown():
    evaluator = EligibilityEvaluator()
    empty_profile = {}

    rule_not_unknown = {
        "rule_id": "r_not_unk",
        "kind": "REQUIRED",
        "expression": {
            "op": "NOT",
            "operands": [
                {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0}
            ],
        },
    }

    res = evaluator.evaluate_rule(rule_not_unknown, empty_profile)
    assert res.status == TriState.UNKNOWN


def test_missing_required_field_aggregates_to_needs_information():
    evaluator = EligibilityEvaluator()
    profile = {
        "citizenship_country": "ETH",
        # gpa is missing!
    }

    rules = [
        {
            "rule_id": "r1",
            "kind": "REQUIRED",
            "expression": {"op": "EQ", "field": "citizenship_country", "value": "ETH"},
        },
        {
            "rule_id": "r2",
            "kind": "REQUIRED",
            "expression": {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
        },
    ]

    result = evaluator.evaluate_rules(rules, profile)
    # Crucial: missing GPA must NOT make the student INELIGIBLE
    assert result.status == EligibilityStatus.NEEDS_INFORMATION
    assert len(result.satisfied_rules) == 1
    assert len(result.unknown_rules) == 1
    assert len(result.failed_rules) == 0
