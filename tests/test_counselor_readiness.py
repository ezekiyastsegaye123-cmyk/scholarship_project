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


def test_application_readiness_unrecorded_profile_yields_unknown():
    """When student profile does not track document preparation, readiness is UNKNOWN."""
    opp = MagicMock()
    req1 = MagicMock(title="Official Secondary School Transcript", kind="REQUIRED", source_evidence_snippet="Transcript required")
    req2 = MagicMock(title="Teacher Recommendation Letter", kind="REQUIRED", source_evidence_snippet="Two recommendations required")
    req3 = MagicMock(title="Optional Art Portfolio", kind="PREFERRED", source_evidence_snippet="Portfolio optional")
    opp.application_requirements = [req1, req2, req3]
    opp.requirements = []

    profile = {}
    ctx = assess_application_readiness(profile, opp)
    assert ctx.level == ReadinessLevel.UNKNOWN
    assert ctx.total_requirements_count == 3
    assert len(ctx.required_components) == 2
    assert "Official Secondary School Transcript" in ctx.required_components
    assert "Teacher Recommendation Letter" in ctx.required_components
    assert "Optional Art Portfolio" in ctx.optional_components


def test_application_readiness_evaluates_prepared_materials():
    """When student profile provides prepared items, assess readiness honestly."""
    opp = MagicMock()
    req1 = MagicMock(title="Official Secondary School Transcript", kind="REQUIRED")
    req2 = MagicMock(title="Teacher Recommendation Letter", kind="REQUIRED")
    opp.application_requirements = [req1, req2]
    opp.requirements = []

    # Student has prepared all required documents
    profile_ready = {"prepared_materials": ["Official Secondary School Transcript", "Teacher Recommendation Letter"]}
    ctx_ready = assess_application_readiness(profile_ready, opp)
    assert ctx_ready.level == ReadinessLevel.READY
    assert len(ctx_ready.missing_components) == 0

    # Student has prepared one document
    profile_partial = {"prepared_materials": ["Official Secondary School Transcript"]}
    ctx_partial = assess_application_readiness(profile_partial, opp)
    assert ctx_partial.level == ReadinessLevel.PARTIALLY_READY
    assert ctx_partial.missing_components == ["Teacher Recommendation Letter"]

    # Student has prepared none
    profile_none = {"prepared_materials": []}
    ctx_none = assess_application_readiness(profile_none, opp)
    assert ctx_none.level == ReadinessLevel.NEEDS_PREPARATION
    assert len(ctx_none.missing_components) == 2
