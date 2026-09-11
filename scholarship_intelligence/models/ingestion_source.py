"""SQLAlchemy model for IngestionSource."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String, Text

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class IngestionSource(Base, TimestampMixin):
    __tablename__ = "ingestion_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    source_domain = Column(String(255), nullable=False, index=True)
    authority_tier = Column(
        String(50),
        CheckConstraint(
            f"authority_tier IN ('{AuthorityTier.OFFICIAL_PROVIDER.value}', '{AuthorityTier.OFFICIAL_UNIVERSITY.value}', '{AuthorityTier.GOVERNMENT.value}', '{AuthorityTier.DISCOVERY_AGGREGATOR.value}', '{AuthorityTier.THIRD_PARTY.value}')"
        ),
        nullable=False,
        default=AuthorityTier.OFFICIAL_UNIVERSITY.value,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    fetch_interval_hours = Column(Integer, nullable=False, default=24)
    last_crawled_at = Column(DateTime, nullable=True)
    last_content_sha256 = Column(String(64), nullable=True)
    last_http_status = Column(Integer, nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
