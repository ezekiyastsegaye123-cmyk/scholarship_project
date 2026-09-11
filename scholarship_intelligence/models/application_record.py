"""SQLAlchemy model for ApplicationRecord.

Tracks student application progress:
- Discrete status states (NOT_STARTED, PLANNING, IN_PROGRESS, SUBMITTED, WITHDRAWN, DECISION_RECEIVED).
- Student private notes (bounded, rendered safely as student-provided).
- Submission date tracking.
- Does not modify canonical scholarship intelligence.
"""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import ApplicationStatus
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class ApplicationRecord(Base, TimestampMixin):
    __tablename__ = "application_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_account_id = Column(
        String(36),
        ForeignKey("student_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id = Column(
        String(36),
        ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(50),
        CheckConstraint(
            f"status IN ('{ApplicationStatus.NOT_STARTED.value}', '{ApplicationStatus.PLANNING.value}', '{ApplicationStatus.IN_PROGRESS.value}', '{ApplicationStatus.SUBMITTED.value}', '{ApplicationStatus.WITHDRAWN.value}', '{ApplicationStatus.DECISION_RECEIVED.value}')"
        ),
        nullable=False,
        default=ApplicationStatus.NOT_STARTED.value,
        index=True,
    )
    student_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_account_id", "opportunity_id", name="uq_student_application_record"),
    )

    # Relationships
    account = relationship("StudentAccount", back_populates="applications")
    opportunity = relationship("ScholarshipOpportunity")
