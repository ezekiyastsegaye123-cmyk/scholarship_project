"""Tests for testing preparedness and application readiness."""
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.enums import ReadinessLevel
from scholarship_intelligence.counselor.rules import (
    assess_application_readiness,
    assess_testing_readiness,
)
from scholarship_intelligence.domain.enums import TriState
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
)


def test_testing_readiness_ready_with_strong_scores():
    opp = MagicMock(requires_sat=TriState.YES.value, requires_act=TriState.UNKNOWN.value)
    profile = {"sat_score": 1480, "english_test_score": 110.0}
    elig_result = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig_result)
    assert ctx.level == ReadinessLevel.READY
    assert ctx.student_sat == 1480


def test_testing_readiness_needs_preparation_when_missing():
    opp = MagicMock(requires_sat=TriState.YES.value, requires_act=TriState.UNKNOWN.value)
    profile = {}  # No test scores
    elig_result = EligibilityEvaluationResult(status=EligibilityStatus.NEEDS_INFORMATION, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig_result)
    assert ctx.level == ReadinessLevel.NEEDS_PREPARATION
    assert "no scores are recorded" in ctx.details[0]


def test_testing_readiness_not_applicable_when_tests_not_required():
    opp = MagicMock(requires_sat=TriState.NO.value, requires_act=TriState.NO.value)
    profile = {}
    elig_result = EligibilityEvaluationResult(status=EligibilityStatus.ELIGIBLE, target_academic_cycle="2026-2027")

    ctx = assess_testing_readiness(profile, opp, elig_result)
    assert ctx.level == ReadinessLevel.NOT_APPLICABLE


def test_application_readiness_lists_required_materials():
    opp = MagicMock()
    req1 = MagicMock(title="Official Secondary School Transcript", kind="REQUIRED", source_evidence_snippet="Transcript required")
    req2 = MagicMock(title="Teacher Recommendation Letter", kind="REQUIRED", source_evidence_snippet="Two recommendations required")
    req3 = MagicMock(title="Optional Art Portfolio", kind="PREFERRED", source_evidence_snippet="Portfolio optional")
    opp.application_requirements = [req1, req2, req3]
    opp.requirements = []

    profile = {}
    ctx = assess_application_readiness(profile, opp)
    assert ctx.level == ReadinessLevel.NEEDS_PREPARATION
    assert ctx.total_requirements_count == 3
    assert len(ctx.required_components) == 2
    assert "Official Secondary School Transcript" in ctx.required_components
    assert "Teacher Recommendation Letter" in ctx.required_components
    assert "Optional Art Portfolio" in ctx.optional_components
