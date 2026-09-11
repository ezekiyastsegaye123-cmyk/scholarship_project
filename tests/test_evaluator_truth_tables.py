"""Comprehensive combinatorial tests for TriState formal truth tables.

Tests every combination of:
- AND (25 cases)
- OR (25 cases)
- NOT (5 cases)
- Multi-operand n-ary conjunction and disjunction
- Commutativity and associativity
"""
import pytest
from scholarship_intelligence.domain.enums import TriState
from scholarship_intelligence.evaluator.logic import (
    AND_TRUTH_TABLE,
    NOT_TRUTH_TABLE,
    OR_TRUTH_TABLE,
    evaluate_and,
    evaluate_and_all,
    evaluate_not,
    evaluate_or,
    evaluate_or_all,
)

ALL_STATES = [
    TriState.YES,
    TriState.NO,
    TriState.UNKNOWN,
    TriState.NOT_APPLICABLE,
    TriState.CONFLICTING,
]


def test_and_truth_table_completeness():
    """Verify all 25 combinations of AND are explicitly defined."""
    assert len(AND_TRUTH_TABLE) == 25
    for s1 in ALL_STATES:
        for s2 in ALL_STATES:
            assert (s1, s2) in AND_TRUTH_TABLE
            res = evaluate_and(s1, s2)
            assert res == AND_TRUTH_TABLE[(s1, s2)]


def test_or_truth_table_completeness():
    """Verify all 25 combinations of OR are explicitly defined."""
    assert len(OR_TRUTH_TABLE) == 25
    for s1 in ALL_STATES:
        for s2 in ALL_STATES:
            assert (s1, s2) in OR_TRUTH_TABLE
            res = evaluate_or(s1, s2)
            assert res == OR_TRUTH_TABLE[(s1, s2)]


def test_not_truth_table_completeness():
    """Verify all 5 states of NOT are explicitly defined."""
    assert len(NOT_TRUTH_TABLE) == 5
    assert evaluate_not(TriState.YES) == TriState.NO
    assert evaluate_not(TriState.NO) == TriState.YES
    assert evaluate_not(TriState.UNKNOWN) == TriState.UNKNOWN
    assert evaluate_not(TriState.NOT_APPLICABLE) == TriState.NOT_APPLICABLE
    assert evaluate_not(TriState.CONFLICTING) == TriState.CONFLICTING


def test_and_absorbing_element_no():
    """Verify NO absorbs in conjunction (false conjunct makes AND false unconditionally)."""
    for s in ALL_STATES:
        assert evaluate_and(TriState.NO, s) == TriState.NO
        assert evaluate_and(s, TriState.NO) == TriState.NO


def test_or_absorbing_element_yes():
    """Verify YES absorbs in disjunction (true disjunct makes OR true unconditionally)."""
    for s in ALL_STATES:
        assert evaluate_or(TriState.YES, s) == TriState.YES
        assert evaluate_or(s, TriState.YES) == TriState.YES


def test_commutativity():
    """Verify AND and OR are commutative across all pairs."""
    for s1 in ALL_STATES:
        for s2 in ALL_STATES:
            assert evaluate_and(s1, s2) == evaluate_and(s2, s1)
            assert evaluate_or(s1, s2) == evaluate_or(s2, s1)


def test_not_applicable_identity_in_and():
    """NOT_APPLICABLE acts as identity in conjunction."""
    assert evaluate_and(TriState.YES, TriState.NOT_APPLICABLE) == TriState.YES
    assert evaluate_and(TriState.NO, TriState.NOT_APPLICABLE) == TriState.NO
    assert evaluate_and(TriState.UNKNOWN, TriState.NOT_APPLICABLE) == TriState.UNKNOWN
    assert evaluate_and(TriState.CONFLICTING, TriState.NOT_APPLICABLE) == TriState.CONFLICTING
    assert evaluate_and(TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE) == TriState.NOT_APPLICABLE


def test_not_applicable_identity_in_or():
    """NOT_APPLICABLE acts as neutral in disjunction."""
    assert evaluate_or(TriState.YES, TriState.NOT_APPLICABLE) == TriState.YES
    assert evaluate_or(TriState.NO, TriState.NOT_APPLICABLE) == TriState.NO
    assert evaluate_or(TriState.UNKNOWN, TriState.NOT_APPLICABLE) == TriState.UNKNOWN
    assert evaluate_or(TriState.CONFLICTING, TriState.NOT_APPLICABLE) == TriState.CONFLICTING
    assert evaluate_or(TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE) == TriState.NOT_APPLICABLE


def test_multi_operand_and():
    """Verify n-ary conjunction behavior."""
    assert evaluate_and_all([]) == TriState.NOT_APPLICABLE
    assert evaluate_and_all([TriState.YES, TriState.YES, TriState.YES]) == TriState.YES
    assert evaluate_and_all([TriState.YES, TriState.YES, TriState.UNKNOWN]) == TriState.UNKNOWN
    assert evaluate_and_all([TriState.YES, TriState.UNKNOWN, TriState.NO]) == TriState.NO
    assert evaluate_and_all([TriState.YES, TriState.CONFLICTING, TriState.UNKNOWN]) == TriState.CONFLICTING
    assert evaluate_and_all([TriState.YES, TriState.NOT_APPLICABLE, TriState.YES]) == TriState.YES
    assert evaluate_and_all([TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE]) == TriState.NOT_APPLICABLE


def test_multi_operand_or():
    """Verify n-ary disjunction behavior."""
    assert evaluate_or_all([]) == TriState.NOT_APPLICABLE
    assert evaluate_or_all([TriState.NO, TriState.NO, TriState.YES]) == TriState.YES
    assert evaluate_or_all([TriState.NO, TriState.UNKNOWN, TriState.NO]) == TriState.UNKNOWN
    assert evaluate_or_all([TriState.NO, TriState.CONFLICTING, TriState.UNKNOWN]) == TriState.CONFLICTING
    assert evaluate_or_all([TriState.NO, TriState.NOT_APPLICABLE, TriState.NO]) == TriState.NO
    assert evaluate_or_all([TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE]) == TriState.NOT_APPLICABLE
