"""Tests for provenance, authority tiers, and source traceability."""
from datetime import datetime
from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.schemas.source import DiscoverySourceCreate, OfficialSourceCreate


def test_authority_tier_hierarchy():
    """Verifies all five authority tiers are defined."""
    assert AuthorityTier.OFFICIAL_PROVIDER.value == "OFFICIAL_PROVIDER"
    assert AuthorityTier.OFFICIAL_UNIVERSITY.value == "OFFICIAL_UNIVERSITY"
    assert AuthorityTier.GOVERNMENT.value == "GOVERNMENT"
    assert AuthorityTier.DISCOVERY_AGGREGATOR.value == "DISCOVERY_AGGREGATOR"
    assert AuthorityTier.THIRD_PARTY.value == "THIRD_PARTY"


def test_official_source_provenance_anchor():
    """Verifies official sources require URL, domain, and verbatim snippet."""
    src = OfficialSourceCreate(
        url="https://www.clarku.edu/financial-aid/scholarships/",
        source_domain="clarku.edu",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        is_primary=True,
        page_title="Scholarships | Clark University",
        extracted_text_snippet="Annual award of $15,000 to $25,000 for four years.",
        last_crawled_at=datetime(2026, 9, 1, 12, 0, 0),
        last_http_status=200,
    )
    assert src.source_domain == "clarku.edu"
    assert src.authority_tier == AuthorityTier.OFFICIAL_UNIVERSITY
    assert len(src.extracted_text_snippet) > 0


def test_discovery_source_lead():
    """Verifies discovery sources track aggregator leads without pretending to be primary."""
    d_src = DiscoverySourceCreate(
        url="https://globalscholarships.com/clark-global-scholars/",
        source_name="Global Scholarships",
        authority_tier=AuthorityTier.DISCOVERY_AGGREGATOR,
        discovery_notes="Used as initial lead before verifying on official university portal.",
    )
    assert d_src.authority_tier == AuthorityTier.DISCOVERY_AGGREGATOR
    assert d_src.source_name == "Global Scholarships"
