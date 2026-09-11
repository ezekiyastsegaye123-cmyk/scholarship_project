"""SQLAlchemy model for conflicting evidence logs."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import ConflictStatus
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class ConflictRecord(Base, TimestampMixin):
    __tablename__ = "conflict_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    source_a_value = Column(Text, nullable=False)
    source_a_url = Column(String(1000), nullable=False)
    source_b_value = Column(Text, nullable=False)
    source_b_url = Column(String(1000), nullable=False)
    resolution_status = Column(
        String(50),
        CheckConstraint(
            f"resolution_status IN ('{ConflictStatus.OPEN.value}', '{ConflictStatus.RESOLVED_OFFICIAL_PREFERRED.value}', '{ConflictStatus.DISMISSED.value}')"
        ),
        nullable=False,
        default=ConflictStatus.OPEN.value,
    )
    resolution_notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="conflict_records")
