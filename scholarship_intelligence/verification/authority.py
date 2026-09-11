"""Source authority classification and deterministic hierarchy ranking."""
from typing import Optional
from urllib.parse import urlparse

from scholarship_intelligence.domain.enums import AuthorityTier

TIER_RANKS = {
    AuthorityTier.OFFICIAL_PROVIDER: 1,
    AuthorityTier.OFFICIAL_UNIVERSITY: 2,
    AuthorityTier.GOVERNMENT: 3,
    AuthorityTier.DISCOVERY_AGGREGATOR: 4,
    AuthorityTier.THIRD_PARTY: 5,
}

KNOWN_AGGREGATOR_DOMAINS = {
    "fastweb.com",
    "scholarships.com",
    "globalscholarships.com",
    "internationalscholarships.com",
    "unigo.com",
    "niche.com",
    "bold.org",
    "scholarshipamerica.org",
    "collegeboard.org",
    "appily.com",
    "cappex.com",
    "petersons.com",
    "iefa.org",
    "wemakescholars.com",
    "scholarshipportal.com",
}

KNOWN_GOV_DOMAINS = {
    "gov",
    "mil",
    "state.gov",
    "ed.gov",
    "usa.gov",
}


def get_authority_rank(tier: AuthorityTier) -> int:
    """Returns integer rank (lower is more authoritative)."""
    return TIER_RANKS.get(tier, 5)


def compare_authority(tier_a: AuthorityTier, tier_b: AuthorityTier) -> int:
    """Compares two authority tiers.
    
    Returns:
        < 0 if tier_a is more authoritative than tier_b
        > 0 if tier_b is more authoritative than tier_a
        0 if tier_a and tier_b have equal authority
    """
    rank_a = get_authority_rank(tier_a)
    rank_b = get_authority_rank(tier_b)
    if rank_a < rank_b:
        return -1
    elif rank_a > rank_b:
        return 1
    return 0


def classify_url_authority(
    url: str,
    provider_domain: Optional[str] = None,
    university_domain: Optional[str] = None,
) -> AuthorityTier:
    """Deterministically classifies a URL into an AuthorityTier based on domain attributes.
    
    Note: AuthorityTier establishes evidentiary hierarchy, but does NOT by itself
    declare facts verified. Fact verification requires direct supporting evidence.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().strip()
    except Exception:
        return AuthorityTier.THIRD_PARTY

    if not hostname:
        return AuthorityTier.THIRD_PARTY

    # Check for known provider domain match
    if provider_domain and (hostname == provider_domain.lower() or hostname.endswith("." + provider_domain.lower())):
        return AuthorityTier.OFFICIAL_PROVIDER

    # Check for known university domain match
    if university_domain and (hostname == university_domain.lower() or hostname.endswith("." + university_domain.lower())):
        return AuthorityTier.OFFICIAL_UNIVERSITY

    # Check for government domains
    parts = hostname.split(".")
    if parts[-1] in KNOWN_GOV_DOMAINS or (len(parts) >= 2 and f"{parts[-2]}.{parts[-1]}" in KNOWN_GOV_DOMAINS):
        return AuthorityTier.GOVERNMENT

    # Check for academic/university domains (.edu or international .ac.uk, .edu.xx)
    if parts[-1] == "edu" or (len(parts) >= 2 and parts[-2] in ("edu", "ac")):
        return AuthorityTier.OFFICIAL_UNIVERSITY

    # Check for known aggregators
    for agg in KNOWN_AGGREGATOR_DOMAINS:
        if hostname == agg or hostname.endswith("." + agg):
            return AuthorityTier.DISCOVERY_AGGREGATOR

    return AuthorityTier.THIRD_PARTY


class AuthorityClassifier:
    """Class wrapper for authority classification operations."""
    classify = staticmethod(classify_url_authority)
    compare = staticmethod(compare_authority)
    get_rank = staticmethod(get_authority_rank)

