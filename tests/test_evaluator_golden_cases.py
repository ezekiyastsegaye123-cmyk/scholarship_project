"""Golden test cases for realistic scholarship eligibility scenarios.

Covers:
- Case A: Clearly Eligible
- Case B: Clearly Ineligible
- Case C: Missing Information (NEEDS_INFORMATION)
- Case D: Conflicting Information (NEEDS_REVIEW)
- Case E: Optional / Preferred condition preservation
- Case F: Verification State Gating
- Case G: Academic Cycle Matching
- Case H: Evidence Provenance in Explanations
"""
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.domain.enums import (
    RuleComparisonOp,
    RuleKind,
    TriState,
    VerificationState,
)
from scholarship_intelligence.domain.rules import EligibilityRuleDefinition
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.schemas.eligibility_eval import EligibilityStatus


@pytest.fixture
def evaluator():
    return EligibilityEvaluator()


@pytest.fixture
def standard_rules():
    return [
        {
            "rule_id": "r_gpa",
            "kind": "REQUIRED",
            "expression": {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
            "source_evidence_snippet": "Applicants must present a cumulative GPA of 3.5 or higher on a 4.0 scale.",
        },
        {
            "rule_id": "r_nationality",
            "kind": "REQUIRED",
            "expression": {"op": "IN", "field": "citizenship_country", "value": ["ETH", "KEN", "UGA"]},
            "source_evidence_snippet": "Open to citizens and permanent residents of Ethiopia, Kenya, and Uganda.",
        },
    ]


def test_golden_case_a_clearly_eligible(evaluator, standard_rules):
    """Case A: All required conditions are satisfied -> ELIGIBLE."""
    profile = {
        "gpa": 3.85,
        "gpa_scale": 4.0,
        "citizenship_country": "ETH",
    }
    result = evaluator.evaluate_rules(standard_rules, profile)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert len(result.satisfied_rules) == 2
    assert len(result.failed_rules) == 0
    assert "ELIGIBLE" in result.explanations[0]


def test_golden_case_b_clearly_ineligible(evaluator, standard_rules):
    """Case B: One required condition is unmet -> INELIGIBLE."""
    profile = {
        "gpa": 3.2,
        "gpa_scale": 4.0,
        "citizenship_country": "ETH",
    }
    result = evaluator.evaluate_rules(standard_rules, profile)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.failed_rules) == 1
    assert result.failed_rules[0].rule_id == "r_gpa"
    assert "Unsatisfied" in result.failed_rules[0].explanation


def test_golden_case_c_missing_information(evaluator, standard_rules):
    """Case C: Required information is missing -> NEEDS_INFORMATION (never INELIGIBLE)."""
    profile = {
        "citizenship_country": "ETH",
        # gpa is not provided
    }
    result = evaluator.evaluate_rules(standard_rules, profile)
    assert result.status == EligibilityStatus.NEEDS_INFORMATION
    assert len(result.unknown_rules) == 1
    assert result.unknown_rules[0].rule_id == "r_gpa"
    assert "Information Needed" in result.unknown_rules[0].explanation


def test_golden_case_d_conflicting_information(evaluator, standard_rules):
    """Case D: Required condition has contradictory data -> NEEDS_REVIEW."""
    profile = {
        "gpa": 3.9,
        "citizenship_country": "ETH",
        "_conflicts": ["citizenship_country"],
    }
    result = evaluator.evaluate_rules(standard_rules, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert len(result.conflicting_rules) == 1
    assert "Unresolved Conflict" in result.conflicting_rules[0].explanation


def test_golden_case_e_preferred_condition(evaluator, standard_rules):
    """Case E: Optional/Preferred rule unmet does NOT disqualify an otherwise eligible student."""
    rules_with_preferred = list(standard_rules) + [
        {
            "rule_id": "r_sat_pref",
            "kind": "PREFERRED",
            "expression": {"op": "GTE", "field": "sat_score", "value": 1500},
            "source_evidence_snippet": "Competitive applicants typically have SAT scores of 1500 or above.",
        }
    ]
    # Student has SAT 1400 (unmet preferred condition), but meets required conditions
    profile = {
        "gpa": 3.8,
        "gpa_scale": 4.0,
        "citizenship_country": "KEN",
        "sat_score": 1400,
    }
    result = evaluator.evaluate_rules(rules_with_preferred, profile)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert len(result.satisfied_rules) == 2
    assert len(result.failed_rules) == 0
    assert len(result.supplementary_rules) == 1
    assert result.supplementary_rules[0].status == TriState.NO


def test_golden_case_f_verification_gating(evaluator):
    """Case F: Unverified, outdated, conflicting, quarantined opportunities are gated."""
    profile = {"gpa": 3.9, "citizenship_country": "ETH"}

    # Mock Opportunity
    opp = MagicMock()
    opp.id = "opp-123"
    opp.title = "Test Opportunity"
    opp.academic_cycle = "2026-2027"

    # 1. UNVERIFIED
    opp.verification_status = VerificationState.UNVERIFIED.value
    res = evaluator.evaluate_opportunity(opp, profile)
    assert res.is_gated is True
    assert res.status == EligibilityStatus.GATED_UNVERIFIED

    # 2. OUTDATED
    opp.verification_status = VerificationState.OUTDATED.value
    res = evaluator.evaluate_opportunity(opp, profile)
    assert res.is_gated is True
    assert res.status == EligibilityStatus.GATED_UNVERIFIED

    # 3. CONFLICTING
    opp.verification_status = VerificationState.CONFLICTING.value
    res = evaluator.evaluate_opportunity(opp, profile)
    assert res.is_gated is True
    assert res.status == EligibilityStatus.NEEDS_REVIEW

    # 4. QUARANTINED_FOR_REVIEW
    opp.verification_status = VerificationState.QUARANTINED_FOR_REVIEW.value
    res = evaluator.evaluate_opportunity(opp, profile)
    assert res.is_gated is True
    assert res.status == EligibilityStatus.NEEDS_REVIEW

    # 5. SOURCE_UNAVAILABLE
    opp.verification_status = VerificationState.SOURCE_UNAVAILABLE.value
    res = evaluator.evaluate_opportunity(opp, profile)
    assert res.is_gated is True
    assert res.status == EligibilityStatus.GATED_UNVERIFIED


def test_golden_case_g_academic_cycle_mismatch(evaluator):
    """Case G: Academic cycle mismatch is gated -> OUTDATED_CYCLE."""
    profile = {"gpa": 3.9, "citizenship_country": "ETH"}
    opp = MagicMock()
    opp.id = "opp-456"
    opp.title = "Past Year Scholarship"
    opp.verification_status = VerificationState.VERIFIED.value
    opp.academic_cycle = "2024-2025"  # Outdated cycle

    res = evaluator.evaluate_opportunity(opp, profile, target_academic_cycle="2026-2027")
    assert res.is_gated is True
    assert res.status == EligibilityStatus.OUTDATED_CYCLE
    assert "Academic cycle mismatch" in res.explanations[0]


def test_golden_case_h_evidence_provenance_in_explanation(evaluator, standard_rules):
    """Case H: Explanation includes source provenance quote and rule ID."""
    profile = {"gpa": 3.1, "citizenship_country": "ETH"}
    result = evaluator.evaluate_rules(standard_rules, profile)

    failed_rule = result.failed_rules[0]
    assert failed_rule.rule_id == "r_gpa"
    assert "Rule: r_gpa" in failed_rule.explanation
    assert "Applicants must present a cumulative GPA of 3.5 or higher" in failed_rule.explanation
