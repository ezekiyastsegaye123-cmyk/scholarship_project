"""SQLAlchemy model for ComparisonSelection.

Persists a student's active scholarship comparison set across sessions and devices.
Enforces:
- Maximum 4 concurrent items (application/service level).
- Unique per (student_account_id, opportunity_id) at database level.
"""
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class ComparisonSelection(Base, TimestampMixin):
    __tablename__ = "comparison_selections"

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

    __table_args__ = (
        UniqueConstraint("student_account_id", "opportunity_id", name="uq_student_comparison_selection"),
    )

    # Relationships
    account = relationship("StudentAccount", back_populates="comparison_selections")
    opportunity = relationship("ScholarshipOpportunity")
