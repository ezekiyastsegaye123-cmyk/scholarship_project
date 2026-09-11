"""SQLAlchemy model for verification history and canonical fact audit trail."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class VerificationHistory(Base, TimestampMixin):
    __tablename__ = "verification_histories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    old_evidence_url = Column(String(1000), nullable=True)
    old_evidence_quote = Column(Text, nullable=True)
    new_evidence_url = Column(String(1000), nullable=True)
    new_evidence_quote = Column(Text, nullable=True)
    decision = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="verification_histories")
