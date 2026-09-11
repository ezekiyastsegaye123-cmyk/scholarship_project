"""Formal multi-valued logic truth tables for TriState evaluations.

Supports:
- YES: Condition verified satisfied.
- NO: Condition verified not satisfied.
- UNKNOWN: Insufficient information to determine outcome. Missing information != NO.
- NOT_APPLICABLE: Condition does not apply to this evaluation context (neutral element).
- CONFLICTING: Unresolved contradictory evidence/data exists.

Formal Axioms:
1. Conjunction (AND):
   - NO is an absorbing element (false conjunct makes conjunction false unconditionally).
   - NOT_APPLICABLE is neutral (identity element) when other conditions exist.
   - CONFLICTING dominates UNKNOWN and YES.
   - UNKNOWN dominates YES.
2. Disjunction (OR):
   - YES is an absorbing element (true disjunct satisfies the disjunction unconditionally).
   - NOT_APPLICABLE is neutral (identity element) when other conditions exist.
   - CONFLICTING dominates UNKNOWN and NO.
   - UNKNOWN dominates NO.
3. Negation (NOT):
   - Inverts YES <-> NO.
   - Fixes UNKNOWN -> UNKNOWN.
   - Fixes NOT_APPLICABLE -> NOT_APPLICABLE.
   - Fixes CONFLICTING -> CONFLICTING.
"""
from typing import Iterable, Sequence
from scholarship_intelligence.domain.enums import TriState


# Explicit 2D Truth Table for Conjunction (AND)
AND_TRUTH_TABLE: dict[tuple[TriState, TriState], TriState] = {
    # (A, B) -> Result
    (TriState.YES, TriState.YES): TriState.YES,
    (TriState.YES, TriState.NO): TriState.NO,
    (TriState.YES, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.YES, TriState.NOT_APPLICABLE): TriState.YES,
    (TriState.YES, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.NO, TriState.YES): TriState.NO,
    (TriState.NO, TriState.NO): TriState.NO,
    (TriState.NO, TriState.UNKNOWN): TriState.NO,
    (TriState.NO, TriState.NOT_APPLICABLE): TriState.NO,
    (TriState.NO, TriState.CONFLICTING): TriState.NO,

    (TriState.UNKNOWN, TriState.YES): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.NO): TriState.NO,
    (TriState.UNKNOWN, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.NOT_APPLICABLE): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.NOT_APPLICABLE, TriState.YES): TriState.YES,
    (TriState.NOT_APPLICABLE, TriState.NO): TriState.NO,
    (TriState.NOT_APPLICABLE, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE): TriState.NOT_APPLICABLE,
    (TriState.NOT_APPLICABLE, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.CONFLICTING, TriState.YES): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.NO): TriState.NO,
    (TriState.CONFLICTING, TriState.UNKNOWN): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.NOT_APPLICABLE): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.CONFLICTING): TriState.CONFLICTING,
}

# Explicit 2D Truth Table for Disjunction (OR)
OR_TRUTH_TABLE: dict[tuple[TriState, TriState], TriState] = {
    # (A, B) -> Result
    (TriState.YES, TriState.YES): TriState.YES,
    (TriState.YES, TriState.NO): TriState.YES,
    (TriState.YES, TriState.UNKNOWN): TriState.YES,
    (TriState.YES, TriState.NOT_APPLICABLE): TriState.YES,
    (TriState.YES, TriState.CONFLICTING): TriState.YES,

    (TriState.NO, TriState.YES): TriState.YES,
    (TriState.NO, TriState.NO): TriState.NO,
    (TriState.NO, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.NO, TriState.NOT_APPLICABLE): TriState.NO,
    (TriState.NO, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.UNKNOWN, TriState.YES): TriState.YES,
    (TriState.UNKNOWN, TriState.NO): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.NOT_APPLICABLE): TriState.UNKNOWN,
    (TriState.UNKNOWN, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.NOT_APPLICABLE, TriState.YES): TriState.YES,
    (TriState.NOT_APPLICABLE, TriState.NO): TriState.NO,
    (TriState.NOT_APPLICABLE, TriState.UNKNOWN): TriState.UNKNOWN,
    (TriState.NOT_APPLICABLE, TriState.NOT_APPLICABLE): TriState.NOT_APPLICABLE,
    (TriState.NOT_APPLICABLE, TriState.CONFLICTING): TriState.CONFLICTING,

    (TriState.CONFLICTING, TriState.YES): TriState.YES,
    (TriState.CONFLICTING, TriState.NO): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.UNKNOWN): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.NOT_APPLICABLE): TriState.CONFLICTING,
    (TriState.CONFLICTING, TriState.CONFLICTING): TriState.CONFLICTING,
}

# Explicit 1D Truth Table for Negation (NOT)
NOT_TRUTH_TABLE: dict[TriState, TriState] = {
    TriState.YES: TriState.NO,
    TriState.NO: TriState.YES,
    TriState.UNKNOWN: TriState.UNKNOWN,
    TriState.NOT_APPLICABLE: TriState.NOT_APPLICABLE,
    TriState.CONFLICTING: TriState.CONFLICTING,
}


def evaluate_not(state: TriState) -> TriState:
    """Evaluate formal negation."""
    return NOT_TRUTH_TABLE[state]


def evaluate_and(left: TriState, right: TriState) -> TriState:
    """Evaluate formal binary conjunction."""
    return AND_TRUTH_TABLE[(left, right)]


def evaluate_or(left: TriState, right: TriState) -> TriState:
    """Evaluate formal binary disjunction."""
    return OR_TRUTH_TABLE[(left, right)]


def evaluate_and_all(operands: Sequence[TriState]) -> TriState:
    """Evaluate n-ary conjunction across sequence of TriState values.
    
    Equivalent to left-fold under AND_TRUTH_TABLE with commutative/associative guarantees.
    """
    if not operands:
        return TriState.NOT_APPLICABLE
    
    # Check absorbing element
    if any(op == TriState.NO for op in operands):
        return TriState.NO
    
    # Check conflicting
    if any(op == TriState.CONFLICTING for op in operands):
        return TriState.CONFLICTING
    
    # Check unknown
    if any(op == TriState.UNKNOWN for op in operands):
        return TriState.UNKNOWN
    
    # Check yes
    if any(op == TriState.YES for op in operands):
        return TriState.YES
    
    # All are NOT_APPLICABLE
    return TriState.NOT_APPLICABLE


def evaluate_or_all(operands: Sequence[TriState]) -> TriState:
    """Evaluate n-ary disjunction across sequence of TriState values.
    
    Equivalent to left-fold under OR_TRUTH_TABLE with commutative/associative guarantees.
    """
    if not operands:
        return TriState.NOT_APPLICABLE
    
    # Check absorbing element
    if any(op == TriState.YES for op in operands):
        return TriState.YES
    
    # Check conflicting
    if any(op == TriState.CONFLICTING for op in operands):
        return TriState.CONFLICTING
    
    # Check unknown
    if any(op == TriState.UNKNOWN for op in operands):
        return TriState.UNKNOWN
    
    # Check no
    if any(op == TriState.NO for op in operands):
        return TriState.NO
    
    # All are NOT_APPLICABLE
    return TriState.NOT_APPLICABLE
