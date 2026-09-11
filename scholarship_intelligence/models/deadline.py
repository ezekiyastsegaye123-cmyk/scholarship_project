"""SQLAlchemy model for application and scholarship deadlines."""
from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import DeadlineType
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class Deadline(Base, TimestampMixin):
    __tablename__ = "deadlines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    deadline_type = Column(
        String(50),
        CheckConstraint(
            f"deadline_type IN ('{DeadlineType.SCHOLARSHIP_APPLICATION.value}', '{DeadlineType.UNIVERSITY_APPLICATION.value}', '{DeadlineType.FINANCIAL_AID.value}', '{DeadlineType.EARLY_ACTION.value}', '{DeadlineType.EARLY_DECISION.value}', '{DeadlineType.REGULAR_DECISION.value}', '{DeadlineType.PRIORITY.value}', '{DeadlineType.ROLLING.value}', '{DeadlineType.NOMINATION.value}', '{DeadlineType.DOCUMENT_SUBMISSION.value}', '{DeadlineType.INTERNATIONAL_STUDENT.value}')"
        ),
        nullable=False,
    )
    deadline_date = Column(Date, nullable=True)
    is_exact_date = Column(Boolean, nullable=False, default=True)
    timezone = Column(String(50), nullable=True, default="America/New_York")
    academic_cycle = Column(String(20), nullable=False, default="2026-2027")
    varies_by_program = Column(Boolean, nullable=False, default=False)
    context_description = Column(Text, nullable=True)
    source_evidence_snippet = Column(Text, nullable=True)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="deadlines")
