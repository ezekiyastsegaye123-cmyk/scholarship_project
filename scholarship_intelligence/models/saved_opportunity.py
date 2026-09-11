"""SQLAlchemy model for SavedOpportunity.

Represents a persistent student reference to an authentic scholarship opportunity.
Crucial invariant: Canonical scholarship intelligence remains untouched.
The saved record only stores the relational link.
"""
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class SavedOpportunity(Base, TimestampMixin):
    __tablename__ = "saved_opportunities"

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
        UniqueConstraint("student_account_id", "opportunity_id", name="uq_student_saved_opportunity"),
    )

    # Relationships
    account = relationship("StudentAccount", back_populates="saved_opportunities")
    opportunity = relationship("ScholarshipOpportunity")
