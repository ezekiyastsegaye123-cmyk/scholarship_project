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
from datetime import date, datetime, timezone
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
    RuleKind,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
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


def test_9_complete_canonical_model_dump_json_determinism():
    """Validates complete bitwise identical serialization without excluding evaluated_at.

    Contract:
    1. assess_opportunity with reference_date anchors evaluated_at deterministically to reference_date 00:00:00 UTC.
    2. model_dump_json() across multiple runs produces bitwise identical strings without field exclusions.
    3. Explicit evaluated_at parameter is preserved and produces bitwise identical model_dump_json().
    """
    counselor = ScholarshipCounselorService()
    profile = {
        "id": "std-det-1",
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "intended_degree_level": "MASTER",
        "intended_destination_country": "US",
        "major": "Mechanical Engineering",
        "gpa": 3.85,
        "gpa_scale": 4.0,
    }
    opp = MagicMock(
        id="opp-det-1",
        title="Engineering Fellowship",
        academic_cycle="2026-2027",
        verification_status=VerificationState.VERIFIED,
        primary_source_url="https://provider.org/fellowship",
        deadlines=[
            MagicMock(
                deadline_date=date(2026, 12, 1),
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
                is_strict=True,
                source_evidence_snippet="Final deadline Dec 1, 2026",
            )
        ],
        funding_details=[
            MagicMock(
                classification=FundingClassification.FULL_FUNDING,
                funding_components=[
                    MagicMock(
                        component_type=FundingComponentType.TUITION,
                        covers_full=True,
                        source_evidence_snippet="Covers full tuition costs",
                    ),
                    MagicMock(
                        component_type=FundingComponentType.STIPEND,
                        covers_full=True,
                        source_evidence_snippet="Provides full monthly living stipend of $2,000",
                    ),
                ],
                source_evidence_snippet="Complete full tuition and living stipend fellowship",
            )
        ],
        eligibility_rules=[
            MagicMock(
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                field_name="gpa",
                comparison_operator="GTE",
                expected_value={"min": 3.5},
                source_evidence_snippet="GPA must be at least 3.5",
            )
        ],
        requirements=[],
    )
    elig = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r1",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="GPA meets criteria",
                field="gpa",
                expected_value=3.5,
                actual_value=3.85,
            )
        ],
    )

    ref_date = date(2026, 11, 1)

    # 1. Verify automatic deterministic timestamp anchoring from reference_date
    res1 = counselor.assess_opportunity(profile, opp, elig, reference_date=ref_date)
    expected_timestamp = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert res1.evaluated_at == expected_timestamp

    # 2. Verify bitwise identical serialization without any exclude set
    canonical_json_1 = res1.model_dump_json()
    for _ in range(50):
        res_i = counselor.assess_opportunity(profile, opp, elig, reference_date=ref_date)
        assert res_i.model_dump_json() == canonical_json_1
        assert res_i.evaluated_at == expected_timestamp

    # 3. Verify explicit evaluated_at timestamp parameterization
    explicit_time = datetime(2026, 11, 1, 14, 45, 30, tzinfo=timezone.utc)
    res_explicit_1 = counselor.assess_opportunity(
        profile, opp, elig, reference_date=ref_date, evaluated_at=explicit_time
    )
    assert res_explicit_1.evaluated_at == explicit_time
    canonical_json_explicit = res_explicit_1.model_dump_json()

    for _ in range(50):
        res_explicit_i = counselor.assess_opportunity(
            profile, opp, elig, reference_date=ref_date, evaluated_at=explicit_time
        )
        assert res_explicit_i.model_dump_json() == canonical_json_explicit
        assert res_explicit_i.evaluated_at == explicit_time

