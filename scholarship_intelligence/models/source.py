"""SQLAlchemy models for sources and provenance tracking."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class OfficialSource(Base, TimestampMixin):
    __tablename__ = "official_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    source_domain = Column(String(255), nullable=False)
    authority_tier = Column(
        String(50),
        CheckConstraint(
            f"authority_tier IN ('{AuthorityTier.OFFICIAL_PROVIDER.value}', '{AuthorityTier.OFFICIAL_UNIVERSITY.value}', '{AuthorityTier.GOVERNMENT.value}', '{AuthorityTier.DISCOVERY_AGGREGATOR.value}', '{AuthorityTier.THIRD_PARTY.value}')"
        ),
        nullable=False,
        default=AuthorityTier.OFFICIAL_UNIVERSITY.value,
    )
    is_primary = Column(Boolean, nullable=False, default=True)
    page_title = Column(String(500), nullable=True)
    extracted_text_snippet = Column(Text, nullable=True)
    last_crawled_at = Column(DateTime, nullable=True)
    last_http_status = Column(Integer, nullable=True)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="official_sources")


class DiscoverySource(Base, TimestampMixin):
    __tablename__ = "discovery_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    source_name = Column(String(255), nullable=False)
    authority_tier = Column(
        String(50),
        CheckConstraint(
            f"authority_tier IN ('{AuthorityTier.OFFICIAL_PROVIDER.value}', '{AuthorityTier.OFFICIAL_UNIVERSITY.value}', '{AuthorityTier.GOVERNMENT.value}', '{AuthorityTier.DISCOVERY_AGGREGATOR.value}', '{AuthorityTier.THIRD_PARTY.value}')"
        ),
        nullable=False,
        default=AuthorityTier.DISCOVERY_AGGREGATOR.value,
    )
    discovery_notes = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="discovery_sources")
