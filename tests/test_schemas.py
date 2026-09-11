"""Tests for Pydantic schema validation of opportunities, providers, and universities."""
import pytest
from pydantic import ValidationError

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    NeedPolicy,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas import (
    AwardCreate,
    DeadlineCreate,
    FundingComponentCreate,
    OfficialSourceCreate,
    ProviderCreate,
    ScholarshipOpportunityCreate,
    UniversityCreate,
)


def test_university_create_valid():
    """Validates UniversityCreate schema."""
    univ = UniversityCreate(
        name="Clark University",
        city="Worcester",
        state="MA",
        country="US",
        admissions_need_policy=NeedPolicy.NEED_AWARE_INTERNATIONAL,
        official_admissions_url="https://www.clarku.edu/admissions/",
    )
    assert univ.name == "Clark University"
    assert univ.admissions_need_policy == NeedPolicy.NEED_AWARE_INTERNATIONAL


def test_provider_create_valid():
    """Validates ProviderCreate schema."""
    prov = ProviderCreate(
        name="Stamps Scholars Program",
        provider_type="FOUNDATION",
        website_url="https://www.stampsscholars.org/",
        country="US",
    )
    assert prov.name == "Stamps Scholars Program"
    assert prov.provider_type == "FOUNDATION"


def test_opportunity_create_nested():
    """Validates full nested opportunity schema."""
    opp = ScholarshipOpportunityCreate(
        title="Berea No-Tuition Promise",
        slug="berea-no-tuition-promise",
        target_degree_level="BACHELOR",
        destination_country="US",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES,
        verification_status=VerificationState.VERIFIED,
        official_sources=[
            OfficialSourceCreate(
                url="https://www.berea.edu/admissions/costs",
                source_domain="berea.edu",
                authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
                is_primary=True,
                extracted_text_snippet="100% funding for all first-year international students.",
            )
        ],
        award=AwardCreate(
            title="Tuition Promise",
            funding_classification=FundingClassification.FULL_FUNDING,
            funding_components=[
                FundingComponentCreate(
                    component_type=FundingComponentType.TUITION,
                    percentage_tuition=100.0,
                )
            ],
        ),
        deadlines=[
            DeadlineCreate(
                deadline_type=DeadlineType.PRIORITY,
                academic_cycle="2026-2027",
            )
        ],
    )
    assert opp.title == "Berea No-Tuition Promise"
    assert len(opp.official_sources) == 1
    assert opp.award.funding_classification == FundingClassification.FULL_FUNDING
    assert len(opp.deadlines) == 1


def test_opportunity_invalid_slug():
    """Rejects empty slug or missing title."""
    with pytest.raises(ValidationError):
        ScholarshipOpportunityCreate(title="Test", slug="")
