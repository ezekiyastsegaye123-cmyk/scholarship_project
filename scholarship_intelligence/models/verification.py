"""SQLAlchemy model for verification audit records."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import VerificationState
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class VerificationRecord(Base, TimestampMixin):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_state = Column(
        String(50),
        CheckConstraint(
            f"verification_state IN ('{VerificationState.VERIFIED.value}', '{VerificationState.PARTIALLY_VERIFIED.value}', '{VerificationState.CONFLICTING.value}', '{VerificationState.OUTDATED.value}', '{VerificationState.UNVERIFIED.value}', '{VerificationState.SOURCE_UNAVAILABLE.value}', '{VerificationState.QUARANTINED_FOR_REVIEW.value}')"
        ),
        nullable=False,
        default=VerificationState.UNVERIFIED.value,
    )
    verifier_identity = Column(String(100), nullable=False)
    verification_method = Column(String(100), nullable=False)
    evidence_url = Column(String(1000), nullable=False)
    evidence_quote = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="verification_records")
