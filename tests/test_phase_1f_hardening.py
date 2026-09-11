"""Phase 1F Final Hardening Pass: Regression & Invariant Tests.

Covers:
1. Full funding + genuine tuition/living evidence -> FULL_FUNDING
2. Full funding + tuition evidence but no living evidence -> NOT FULL_FUNDING (FULL_TUITION)
3. Full funding + component types but all evidence missing -> NOT FULL_FUNDING
4. Full funding + placeholder evidence -> NOT FULL_FUNDING
5. Full tuition with genuine tuition evidence -> FULL_TUITION
6. Explicit reference_date produces deterministic deadline state
7. Missing reference_date cannot silently use date.today() (raises ValueError)
8. AST check proving zero calls to date.today() in counselor codebase.
"""
import ast
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from scholarship_intelligence.counselor.rules import (
    assess_deadlines,
    assess_funding,
    is_genuine_evidence,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    DeadlineReadiness,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
)


@pytest.fixture
def counselor():
    return ScholarshipCounselorService()


# ==============================================================================
# ISSUE 2: FULL FUNDING EVIDENCE SUBSTANTIATION TESTS
# ==============================================================================

def test_1_full_funding_with_genuine_tuition_and_living_evidence():
    """Case A: Full funding classification with genuine evidence for tuition and living support -> FULL_FUNDING."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=88000.0,
        funding_components=[
            MagicMock(
                component_type=FundingComponentType.TUITION.value,
                source_evidence_snippet="Full tuition and mandatory fees covered for 4 undergraduate years.",
            ),
            MagicMock(
                component_type=FundingComponentType.ROOM.value,
                source_evidence_snippet="Standard on-campus room housing provided in university residence halls.",
            ),
            MagicMock(
                component_type=FundingComponentType.MEALS.value,
                source_evidence_snippet="Full unlimited dining meal plan included each semester.",
            ),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_FUNDING
    assert ctx.tuition_covered == TriState.YES
    assert ctx.living_expenses_covered == TriState.YES
    assert "Full funding" in ctx.summary
    assert "tuition as well as living, room, and board" in ctx.summary


def test_2_full_funding_label_with_tuition_evidence_but_no_living_evidence_downgrades():
    """Case B: Full funding label with tuition evidence but unevidenced living support -> NOT FULL_FUNDING (FULL_TUITION)."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=88000.0,
        funding_components=[
            MagicMock(
                component_type=FundingComponentType.TUITION.value,
                source_evidence_snippet="100% full tuition scholarship.",
            ),
            MagicMock(
                component_type=FundingComponentType.ROOM.value,
                source_evidence_snippet=None,  # No evidence
            ),
            MagicMock(
                component_type=FundingComponentType.MEALS.value,
                source_evidence_snippet=None,  # No evidence
            ),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification != FundingClassification.FULL_FUNDING
    assert ctx.funding_classification == FundingClassification.FULL_TUITION
    assert "Full tuition only" in ctx.summary
    assert "Room, meals, and living expenses are NOT verified as covered" in ctx.summary


def test_3_full_funding_with_components_but_all_evidence_missing_rejected():
    """Case C: Components exist (tuition, room, meals) but all evidence snippets are None -> NOT FULL_FUNDING."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=88000.0,
        funding_components=[
            MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet=None),
            MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet=None),
            MagicMock(component_type=FundingComponentType.MEALS.value, source_evidence_snippet=None),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification != FundingClassification.FULL_FUNDING
    assert "Unconfirmed full funding" in ctx.summary
    assert any("unevidenced" in d.lower() or "placeholder" in d.lower() for d in ctx.details)


def test_4_full_funding_with_placeholder_evidence_rejected():
    """Case D: Components have generic filler placeholder strings as evidence -> NOT FULL_FUNDING."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_FUNDING.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=88000.0,
        funding_components=[
            MagicMock(
                component_type=FundingComponentType.TUITION.value,
                source_evidence_snippet="Primary authoritative opportunity source",
            ),
            MagicMock(
                component_type=FundingComponentType.ROOM.value,
                source_evidence_snippet="Verified source",
            ),
            MagicMock(
                component_type=FundingComponentType.MEALS.value,
                source_evidence_snippet="Funding evidence",
            ),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification != FundingClassification.FULL_FUNDING
    assert "Unconfirmed full funding" in ctx.summary
    assert any("placeholder" in d.lower() or "unevidenced" in d.lower() for d in ctx.details)


def test_5_full_tuition_with_genuine_tuition_evidence():
    """Case 5: Full tuition award with genuine tuition evidence -> FULL_TUITION."""
    opp = MagicMock()
    award = MagicMock(
        funding_classification=FundingClassification.FULL_TUITION.value,
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=55000.0,
        funding_components=[
            MagicMock(
                component_type=FundingComponentType.TUITION.value,
                source_evidence_snippet="Covers full undergraduate tuition charges for academic years 1 through 4.",
            ),
        ],
    )
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_TUITION
    assert ctx.tuition_covered == TriState.YES
    assert "Full tuition only" in ctx.summary


def test_is_genuine_evidence_rejection_rules():
    """Validates the helper rejecting None, empty, whitespace, and known placeholders."""
    assert is_genuine_evidence(None) is False
    assert is_genuine_evidence("") is False
    assert is_genuine_evidence("   ") is False
    assert is_genuine_evidence("Primary authoritative opportunity source") is False
    assert is_genuine_evidence("Verified source") is False
    assert is_genuine_evidence("Funding evidence") is False
    assert is_genuine_evidence("Official source") is False
    assert is_genuine_evidence("Official provider source") is False
    assert is_genuine_evidence("None") is False
    assert is_genuine_evidence("null") is False
    assert is_genuine_evidence("N/A") is False

    # Genuine text passes
    assert is_genuine_evidence("Full tuition scholarship for international students.") is True
    assert is_genuine_evidence("Room and board included in scholarship package.") is True


# ==============================================================================
# ISSUE 1: MACHINE-CLOCK REMOVAL & DETERMINISTIC DEADLINE TESTS
# ==============================================================================

def test_6_explicit_reference_date_produces_deterministic_deadline_state():
    """Case 6: Deadline evaluation depends exclusively on supplied reference_date and deadline data."""
    opp = MagicMock()
    deadline = MagicMock(
        deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
        deadline_date=date(2027, 2, 1),
        is_exact_date=True,
        timezone="America/New_York",
        context_description="Scholarship priority deadline",
        source_evidence_snippet="Deadline is February 1, 2027.",
    )
    opp.deadlines = [deadline]

    # Reference date 20 days prior -> OPEN
    ctx_open = assess_deadlines(opp, reference_date=date(2027, 1, 12))
    assert ctx_open.deadlines[0].readiness == DeadlineReadiness.OPEN
    assert ctx_open.deadlines[0].days_remaining == 20

    # Reference date 10 days prior -> CLOSING_SOON (<= 14 days)
    ctx_closing = assess_deadlines(opp, reference_date=date(2027, 1, 22))
    assert ctx_closing.deadlines[0].readiness == DeadlineReadiness.CLOSING_SOON
    assert ctx_closing.deadlines[0].days_remaining == 10

    # Reference date 2 days past -> CLOSED (< 0 days)
    ctx_closed = assess_deadlines(opp, reference_date=date(2027, 2, 3))
    assert ctx_closed.deadlines[0].readiness == DeadlineReadiness.CLOSED
    assert ctx_closed.deadlines[0].days_remaining == -2


def test_7_missing_reference_date_cannot_silently_use_date_today(counselor):
    """Case 7: Missing reference_date cannot silently read machine clock; must raise explicit ValueError."""
    opp = MagicMock(
        id="opp-clock-test",
        title="Clock Test Award",
        verification_status=VerificationState.VERIFIED.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        is_open_to_all_majors=True,
        official_sources=[],
        deadlines=[
            MagicMock(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION.value,
                deadline_date=date(2027, 3, 1),
                is_exact_date=True,
            )
        ],
        application_requirements=[],
        requirements=[],
        award=None,
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )

    # 1. Direct assess_deadlines call without reference_date must raise ValueError
    with pytest.raises(ValueError, match="reference_date is required"):
        assess_deadlines(opp)

    with pytest.raises(ValueError, match="reference_date is required"):
        assess_deadlines(opp, reference_date=None)

    # 2. Counselor assess_opportunity on opportunity with deadlines without reference_date must raise ValueError
    with pytest.raises(ValueError, match="reference_date is required"):
        counselor.assess_opportunity({}, opp, elig)

    with pytest.raises(ValueError, match="reference_date is required"):
        counselor.assess_opportunity({}, opp, elig, reference_date=None)


def test_8_zero_date_today_calls_in_counselor_codebase():
    """Static AST verification: Confirms date.today() does NOT exist anywhere in the counselor codebase."""
    counselor_dir = Path("scholarship_intelligence/counselor")
    for py_file in counselor_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for direct today() or date.today() calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == "today":
                    pytest.fail(f"Prohibited call 'today()' found in {py_file} at line {node.lineno}")
                elif isinstance(node.func, ast.Name) and node.func.id == "today":
                    pytest.fail(f"Prohibited call 'today()' found in {py_file} at line {node.lineno}")
