"""Tests for qualitative academic, geographic, and program alignment assessments."""
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.enums import AlignmentLevel
from scholarship_intelligence.counselor.rules import (
    assess_academic_alignment,
    assess_geographic_alignment,
    assess_program_alignment,
)
from scholarship_intelligence.domain.enums import RuleKind, TriState
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


@pytest.fixture
def mock_opp():
    opp = MagicMock()
    opp.id = "opp-1"
    opp.title = "Academic Excellence Scholarship"
    opp.international_students_allowed = TriState.YES.value
    return opp


def test_academic_alignment_strong_when_gpa_satisfied(mock_opp):
    profile = {"gpa": 3.85, "gpa_scale": 4.0}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="GPA meets requirement",
                field="gpa",
                expected_value=3.5,
                actual_value=3.85,
                scale=4.0,
            )
        ],
    )
    ctx = assess_academic_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.STRONG
    assert ctx.student_gpa == 3.85
    assert ctx.required_gpa == 3.5
    assert "meets or exceeds" in ctx.details[0]


def test_academic_alignment_limited_when_gpa_unsatisfied(mock_opp):
    profile = {"gpa": 3.1, "gpa_scale": 4.0}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.INELIGIBLE,
        target_academic_cycle="2026-2027",
        failed_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.NO,
                explanation="GPA below minimum",
                field="gpa",
                expected_value=3.5,
                actual_value=3.1,
                scale=4.0,
            )
        ],
    )
    ctx = assess_academic_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.LIMITED
    assert "below the published minimum" in ctx.details[0]


def test_academic_alignment_unknown_when_gpa_missing(mock_opp):
    profile = {}  # Missing GPA
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.NEEDS_INFORMATION,
        target_academic_cycle="2026-2027",
        unknown_rules=[
            RuleEvaluationResult(
                rule_id="r_gpa",
                kind=RuleKind.REQUIRED,
                status=TriState.UNKNOWN,
                explanation="GPA not provided",
                field="gpa",
                expected_value=3.5,
                scale=4.0,
            )
        ],
    )
    ctx = assess_academic_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.UNKNOWN
    assert "not provided" in ctx.details[0]


def test_geographic_alignment_strong_matching_country(mock_opp):
    profile = {"citizenship_country": "ETH", "residence_country": "ETH"}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
        satisfied_rules=[
            RuleEvaluationResult(
                rule_id="r_geo",
                kind=RuleKind.REQUIRED,
                status=TriState.YES,
                explanation="Eligible country",
                field="citizenship_country",
                expected_value=["ETH", "KEN"],
                actual_value="ETH",
            )
        ],
    )
    ctx = assess_geographic_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.STRONG
    assert "matches published eligible geographic criteria" in ctx.details[0]


def test_geographic_alignment_limited_non_matching(mock_opp):
    profile = {"citizenship_country": "NGA"}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.INELIGIBLE,
        target_academic_cycle="2026-2027",
        failed_rules=[
            RuleEvaluationResult(
                rule_id="r_geo",
                kind=RuleKind.REQUIRED,
                status=TriState.NO,
                explanation="Not in country list",
                field="citizenship_country",
                expected_value=["ETH", "KEN"],
                actual_value="NGA",
            )
        ],
    )
    ctx = assess_geographic_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.LIMITED
    assert "outside published eligible countries" in ctx.details[0]


def test_program_alignment_not_assessable_when_no_restriction(mock_opp):
    profile = {"intended_major": "Computer Science"}
    elig_result = EligibilityEvaluationResult(
        status=EligibilityStatus.ELIGIBLE,
        target_academic_cycle="2026-2027",
    )
    ctx = assess_program_alignment(profile, mock_opp, elig_result)
    assert ctx.level == AlignmentLevel.NOT_ASSESSABLE
    assert ctx.has_major_restriction is False
    assert "open across all undergraduate fields" in ctx.details[0]
