"""Deterministic Freshness Classifier for scholarship opportunities."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from scholarship_intelligence.domain.enums import VerificationState
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity


class FreshnessLevel(str, Enum):
    """Deterministic freshness classification levels."""
    FRESH = "FRESH"          # <= 30 days
    MODERATE = "MODERATE"    # 31 to 90 days
    STALE = "STALE"          # > 90 days
    UNVERIFIED = "UNVERIFIED"


class FreshnessResult(BaseModel):
    """Structured assessment of data freshness."""
    level: FreshnessLevel
    days_since_crawl: Optional[int] = None
    days_since_verification: Optional[int] = None
    last_crawled_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    is_stale: bool = False
    message: str


class FreshnessClassifier:
    """Classifies opportunity freshness deterministically without machine clock drift."""

    FRESH_THRESHOLD_DAYS = 30
    MODERATE_THRESHOLD_DAYS = 90

    @classmethod
    def classify(
        cls,
        opportunity: ScholarshipOpportunity,
        reference_time: Optional[datetime] = None,
    ) -> FreshnessResult:
        """Evaluates opportunity freshness against explicit threshold boundaries."""
        ref_time = reference_time or datetime.now(timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        # 1. Determine most recent crawl time across official sources
        last_crawled_at: Optional[datetime] = None
        for s in opportunity.official_sources:
            if s.last_crawled_at:
                c_at = s.last_crawled_at
                if c_at.tzinfo is None:
                    c_at = c_at.replace(tzinfo=timezone.utc)
                if last_crawled_at is None or c_at > last_crawled_at:
                    last_crawled_at = c_at

        # 2. Determine most recent verification time
        last_verified_at: Optional[datetime] = None
        for v in opportunity.verification_records:
            if v.verified_at:
                v_at = v.verified_at
                if v_at.tzinfo is None:
                    v_at = v_at.replace(tzinfo=timezone.utc)
                if last_verified_at is None or v_at > last_verified_at:
                    last_verified_at = v_at

        days_crawl = None
        if last_crawled_at:
            delta_crawl = ref_time - last_crawled_at
            days_crawl = max(0, delta_crawl.days)

        days_verif = None
        if last_verified_at:
            delta_verif = ref_time - last_verified_at
            days_verif = max(0, delta_verif.days)

        # If unverified or no verification record exists
        if opportunity.verification_status == VerificationState.UNVERIFIED.value or last_verified_at is None:
            return FreshnessResult(
                level=FreshnessLevel.UNVERIFIED,
                days_since_crawl=days_crawl,
                days_since_verification=days_verif,
                last_crawled_at=last_crawled_at,
                last_verified_at=last_verified_at,
                is_stale=True,
                message="Opportunity has never been verified.",
            )

        # Baseline comparison uses days_verif (or days_crawl if available)
        effective_days = days_verif if days_verif is not None else (days_crawl or 999)

        if effective_days <= cls.FRESH_THRESHOLD_DAYS:
            return FreshnessResult(
                level=FreshnessLevel.FRESH,
                days_since_crawl=days_crawl,
                days_since_verification=days_verif,
                last_crawled_at=last_crawled_at,
                last_verified_at=last_verified_at,
                is_stale=False,
                message=f"Verified within the last {effective_days} days (threshold: <= {cls.FRESH_THRESHOLD_DAYS} days).",
            )
        elif effective_days <= cls.MODERATE_THRESHOLD_DAYS:
            return FreshnessResult(
                level=FreshnessLevel.MODERATE,
                days_since_crawl=days_crawl,
                days_since_verification=days_verif,
                last_crawled_at=last_crawled_at,
                last_verified_at=last_verified_at,
                is_stale=False,
                message=f"Verified {effective_days} days ago (within moderate threshold: 31-{cls.MODERATE_THRESHOLD_DAYS} days).",
            )
        else:
            return FreshnessResult(
                level=FreshnessLevel.STALE,
                days_since_crawl=days_crawl,
                days_since_verification=days_verif,
                last_crawled_at=last_crawled_at,
                last_verified_at=last_verified_at,
                is_stale=True,
                message=f"Opportunity verified {effective_days} days ago (> {cls.MODERATE_THRESHOLD_DAYS} days threshold). Re-verification required.",
            )
