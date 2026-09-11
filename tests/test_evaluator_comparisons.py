"""Tests for evaluator comparison and membership operators."""
import pytest
from scholarship_intelligence.domain.enums import RuleComparisonOp, TriState
from scholarship_intelligence.evaluator.operators import evaluate_comparison


def test_gpa_numeric_comparisons():
    # GTE
    st, _ = evaluate_comparison(RuleComparisonOp.GTE, "gpa", 3.5, 3.8, 4.0, 4.0)
    assert st == TriState.YES

    st, _ = evaluate_comparison(RuleComparisonOp.GTE, "gpa", 3.5, 3.5, 4.0, 4.0)
    assert st == TriState.YES

    st, _ = evaluate_comparison(RuleComparisonOp.GTE, "gpa", 3.5, 3.2, 4.0, 4.0)
    assert st == TriState.NO

    # GT
    st, _ = evaluate_comparison(RuleComparisonOp.GT, "gpa", 3.5, 3.5, 4.0, 4.0)
    assert st == TriState.NO

    st, _ = evaluate_comparison(RuleComparisonOp.GT, "gpa", 3.5, 3.6, 4.0, 4.0)
    assert st == TriState.YES

    # LT / LTE
    st, _ = evaluate_comparison(RuleComparisonOp.LTE, "gpa", 3.5, 3.5, 4.0, 4.0)
    assert st == TriState.YES

    st, _ = evaluate_comparison(RuleComparisonOp.LT, "gpa", 3.5, 3.5, 4.0, 4.0)
    assert st == TriState.NO


def test_gpa_scale_mismatch_returns_unknown():
    """Scale mismatch without defined conversion rule must return UNKNOWN, not guess."""
    st, reason = evaluate_comparison(
        RuleComparisonOp.GTE, "gpa", 3.5, 18.0, expected_scale=4.0, student_scale=20.0
    )
    assert st == TriState.UNKNOWN
    assert "scale mismatch" in reason.lower()


def test_membership_in_operator():
    # Allowed country
    st, _ = evaluate_comparison(
        RuleComparisonOp.IN, "citizenship_country", ["ETH", "KEN", "UGA"], "ETH"
    )
    assert st == TriState.YES

    # Disallowed country
    st, _ = evaluate_comparison(
        RuleComparisonOp.IN, "citizenship_country", ["ETH", "KEN", "UGA"], "NGA"
    )
    assert st == TriState.NO

    # Country alias matching (Ethiopia == ETH == ET)
    st, _ = evaluate_comparison(
        RuleComparisonOp.IN, "citizenship_country", ["Ethiopia", "Kenya"], "ETH"
    )
    assert st == TriState.YES


def test_containment_contains_operator():
    # List containment
    interests = ["computer science", "artificial intelligence", "robotics"]
    st, _ = evaluate_comparison(
        RuleComparisonOp.CONTAINS, "interests", "computer science", interests
    )
    assert st == TriState.YES

    st, _ = evaluate_comparison(
        RuleComparisonOp.CONTAINS, "interests", "history", interests
    )
    assert st == TriState.NO

    # String containment
    major = "Computer Science and Mathematics"
    st, _ = evaluate_comparison(
        RuleComparisonOp.CONTAINS, "intended_major", "Computer Science", major
    )
    assert st == TriState.YES


def test_missing_student_value_returns_unknown():
    """Any comparison with a missing student value must return UNKNOWN, never NO."""
    for op in (RuleComparisonOp.EQ, RuleComparisonOp.GTE, RuleComparisonOp.IN, RuleComparisonOp.CONTAINS):
        st, _ = evaluate_comparison(op, "gpa", 3.5, None)
        assert st == TriState.UNKNOWN
