"""SQLAlchemy model for scholarship providers / foundations."""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    website_url = Column(String(1000), nullable=True)
    country = Column(String(3), nullable=False, default="US")
    description = Column(Text, nullable=True)

    # Relationships
    opportunities = relationship("ScholarshipOpportunity", back_populates="provider")
