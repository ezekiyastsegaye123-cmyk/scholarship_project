"""Tests for funding models and decomposed funding components."""
from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    FundingClassification,
    FundingComponentType,
    TriState,
)
from scholarship_intelligence.schemas.funding import AwardCreate, FundingComponentCreate


def test_funding_classification_values():
    """Verifies all required funding classifications exist."""
    assert FundingClassification.FULL_FUNDING.value == "FULL_FUNDING"
    assert FundingClassification.FULL_TUITION.value == "FULL_TUITION"
    assert FundingClassification.PARTIAL_FUNDING.value == "PARTIAL_FUNDING"
    assert FundingClassification.STIPEND_ONLY.value == "STIPEND_ONLY"
    assert FundingClassification.FEES_ONLY.value == "FEES_ONLY"
    assert FundingClassification.UNKNOWN.value == "UNKNOWN"


def test_decomposed_funding_components():
    """Validates decomposing an award into multiple distinct funding components."""
    award = AwardCreate(
        title="Comprehensive International Excellence Award",
        funding_classification=FundingClassification.FULL_FUNDING,
        is_renewable=TriState.YES,
        renewal_criteria="Maintain 3.2 GPA",
        estimated_annual_value_usd=80000.0,
        funding_components=[
            FundingComponentCreate(
                component_type=FundingComponentType.TUITION,
                percentage_tuition=100.0,
                currency="USD",
                amount_period=AmountPeriod.ANNUAL,
                description="100% undergraduate tuition waiver.",
            ),
            FundingComponentCreate(
                component_type=FundingComponentType.ROOM,
                amount_min=12000.0,
                amount_max=14000.0,
                currency="USD",
                amount_period=AmountPeriod.ANNUAL,
                description="On-campus housing credit.",
            ),
            FundingComponentCreate(
                component_type=FundingComponentType.STIPEND,
                amount_min=5000.0,
                amount_max=5000.0,
                currency="USD",
                amount_period=AmountPeriod.ONE_TIME,
                description="One-time research and travel stipend.",
            ),
        ],
    )
    assert len(award.funding_components) == 3
    assert award.funding_components[0].component_type == FundingComponentType.TUITION
    assert award.funding_components[1].component_type == FundingComponentType.ROOM
    assert award.funding_components[2].component_type == FundingComponentType.STIPEND
    assert award.funding_components[2].amount_period == AmountPeriod.ONE_TIME
