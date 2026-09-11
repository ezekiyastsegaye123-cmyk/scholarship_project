"""SQLAlchemy model for higher education institutions."""
from sqlalchemy import CheckConstraint, Column, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import NeedPolicy
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class University(Base, TimestampMixin):
    __tablename__ = "universities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True, index=True)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    country = Column(String(3), nullable=False, default="US")
    admissions_need_policy = Column(
        String(50),
        CheckConstraint(
            f"admissions_need_policy IN ('{NeedPolicy.NEED_BLIND_INTERNATIONAL.value}', '{NeedPolicy.NEED_AWARE_INTERNATIONAL.value}', '{NeedPolicy.NO_AID_INTERNATIONAL.value}', '{NeedPolicy.UNKNOWN.value}')"
        ),
        nullable=False,
        default=NeedPolicy.UNKNOWN.value,
    )
    official_admissions_url = Column(String(1000), nullable=True)
    official_financial_aid_url = Column(String(1000), nullable=True)

    # Relationships
    opportunities = relationship("ScholarshipOpportunity", back_populates="university")
