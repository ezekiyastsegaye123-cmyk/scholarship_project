"""Tests for Phase 1C source authority classification and hierarchy ranking."""
import pytest
from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.verification.authority import (
    AuthorityClassifier,
    classify_url_authority,
    compare_authority,
    get_authority_rank,
)


def test_all_five_authority_tiers_ranked_deterministically():
    assert get_authority_rank(AuthorityTier.OFFICIAL_PROVIDER) == 1
    assert get_authority_rank(AuthorityTier.OFFICIAL_UNIVERSITY) == 2
    assert get_authority_rank(AuthorityTier.GOVERNMENT) == 3
    assert get_authority_rank(AuthorityTier.DISCOVERY_AGGREGATOR) == 4
    assert get_authority_rank(AuthorityTier.THIRD_PARTY) == 5


def test_compare_authority_hierarchy():
    # Provider outranks University
    assert compare_authority(AuthorityTier.OFFICIAL_PROVIDER, AuthorityTier.OFFICIAL_UNIVERSITY) < 0
    # University outranks Aggregator
    assert compare_authority(AuthorityTier.OFFICIAL_UNIVERSITY, AuthorityTier.DISCOVERY_AGGREGATOR) < 0
    # Aggregator outranks Third Party
    assert compare_authority(AuthorityTier.DISCOVERY_AGGREGATOR, AuthorityTier.THIRD_PARTY) < 0
    # Equal tiers
    assert compare_authority(AuthorityTier.OFFICIAL_UNIVERSITY, AuthorityTier.OFFICIAL_UNIVERSITY) == 0


def test_domain_authority_classification():
    # .edu domain
    assert classify_url_authority("https://admissions.harvard.edu/aid") == AuthorityTier.OFFICIAL_UNIVERSITY
    assert classify_url_authority("https://www.berea.edu/costs") == AuthorityTier.OFFICIAL_UNIVERSITY
    assert classify_url_authority("https://ox.ac.uk/scholarships") == AuthorityTier.OFFICIAL_UNIVERSITY

    # Government domain
    assert classify_url_authority("https://travel.state.gov/visa") == AuthorityTier.GOVERNMENT
    assert classify_url_authority("https://studentaid.ed.gov/fafsa") == AuthorityTier.GOVERNMENT

    # Provider domain match
    assert (
        classify_url_authority("https://www.gatesfoundation.org/our-work", provider_domain="gatesfoundation.org")
        == AuthorityTier.OFFICIAL_PROVIDER
    )

    # University domain match (even if non-.edu)
    assert (
        classify_url_authority("https://www.soka.ac.jp/en/admissions", university_domain="soka.ac.jp")
        == AuthorityTier.OFFICIAL_UNIVERSITY
    )

    # Known aggregators
    assert classify_url_authority("https://www.fastweb.com/college-scholarships") == AuthorityTier.DISCOVERY_AGGREGATOR
    assert classify_url_authority("https://globalscholarships.com/clark-scholars") == AuthorityTier.DISCOVERY_AGGREGATOR
    assert classify_url_authority("https://bold.org/scholarships") == AuthorityTier.DISCOVERY_AGGREGATOR

    # Third party blog
    assert classify_url_authority("https://randomstudentblog.wordpress.com/my-essay") == AuthorityTier.THIRD_PARTY
