"""Tests for counselor funding decomposition and the full tuition != full funding invariant."""
from unittest.mock import MagicMock
import pytest
from scholarship_intelligence.counselor.rules import assess_funding
from scholarship_intelligence.domain.enums import (
    FundingClassification,
    FundingComponentType,
    TriState,
)


def test_full_tuition_does_not_equal_full_funding():
    """Critical Invariant: Full tuition award must not be presented as fully funded."""
    opp = MagicMock()
    award = MagicMock()
    award.funding_classification = FundingClassification.FULL_TUITION.value
    award.is_renewable = TriState.YES.value
    award.estimated_annual_value_usd = 60000.0

    # Only tuition component is verified
    comp_tuition = MagicMock()
    comp_tuition.component_type = FundingComponentType.TUITION.value
    comp_tuition.source_evidence_snippet = "100% tuition coverage for four years."
    award.funding_components = [comp_tuition]
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_TUITION
    assert ctx.tuition_covered == TriState.YES
    assert ctx.living_expenses_covered == TriState.UNKNOWN
    # Must explicitly state living costs are NOT verified as covered
    assert "Full tuition only" in ctx.summary
    assert "Room, meals, and living expenses are NOT verified as covered" in ctx.summary


def test_full_funding_comprehensive():
    """Comprehensive award covering tuition, room, meals, and living expenses."""
    opp = MagicMock()
    award = MagicMock()
    award.funding_classification = FundingClassification.FULL_FUNDING.value
    award.is_renewable = TriState.YES.value
    award.estimated_annual_value_usd = 85000.0

    comp_t = MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="Full tuition")
    comp_r = MagicMock(component_type=FundingComponentType.ROOM.value, source_evidence_snippet="Room covered")
    comp_m = MagicMock(component_type=FundingComponentType.MEALS.value, source_evidence_snippet="Board covered")
    comp_l = MagicMock(component_type=FundingComponentType.LIVING_EXPENSES.value, source_evidence_snippet="Monthly stipend")
    award.funding_components = [comp_t, comp_r, comp_m, comp_l]
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.FULL_FUNDING
    assert ctx.tuition_covered == TriState.YES
    assert ctx.living_expenses_covered == TriState.YES
    assert ctx.room_covered == TriState.YES if hasattr(ctx, "room_covered") else True
    assert "Full funding" in ctx.summary
    assert "tuition as well as living, room, and board" in ctx.summary


def test_partial_funding():
    opp = MagicMock()
    award = MagicMock()
    award.funding_classification = FundingClassification.PARTIAL_FUNDING.value
    award.is_renewable = TriState.NO.value
    award.estimated_annual_value_usd = 15000.0
    comp_t = MagicMock(component_type=FundingComponentType.TUITION.value, source_evidence_snippet="$15,000 tuition grant")
    award.funding_components = [comp_t]
    opp.award = award

    ctx = assess_funding(opp)
    assert ctx.funding_classification == FundingClassification.PARTIAL_FUNDING
    assert "Partial funding" in ctx.summary
