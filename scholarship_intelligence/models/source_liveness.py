"""SQLAlchemy model for source liveness and soft-404 inspection logs."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class SourceLivenessLog(Base, TimestampMixin):
    __tablename__ = "source_liveness_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=True, index=True)
    source_url = Column(String(1000), nullable=False, index=True)
    liveness_status = Column(String(50), nullable=False)
    http_status = Column(Integer, nullable=True)
    final_url = Column(String(1000), nullable=True)
    redirect_chain_json = Column(Text, nullable=True)
    content_sha256 = Column(String(64), nullable=True)
    content_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="source_liveness_logs")
