"""SQLAlchemy models for awards and funding components."""
from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    FundingClassification,
    FundingComponentType,
    TriState,
)
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class Award(Base, TimestampMixin):
    __tablename__ = "awards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    funding_classification = Column(
        String(50),
        CheckConstraint(
            f"funding_classification IN ('{FundingClassification.FULL_FUNDING.value}', '{FundingClassification.FULL_TUITION.value}', '{FundingClassification.PARTIAL_FUNDING.value}', '{FundingClassification.STIPEND_ONLY.value}', '{FundingClassification.FEES_ONLY.value}', '{FundingClassification.UNKNOWN.value}')"
        ),
        nullable=False,
        default=FundingClassification.UNKNOWN.value,
    )
    title = Column(String(255), nullable=False)
    is_renewable = Column(
        String(20),
        CheckConstraint(
            f"is_renewable IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )
    renewal_criteria = Column(Text, nullable=True)
    estimated_annual_value_usd = Column(Float, nullable=True)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="award")
    funding_components = relationship("FundingComponent", back_populates="award", cascade="all, delete-orphan")


class FundingComponent(Base, TimestampMixin):
    __tablename__ = "funding_components"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    award_id = Column(String(36), ForeignKey("awards.id", ondelete="CASCADE"), nullable=False, index=True)
    component_type = Column(
        String(50),
        CheckConstraint(
            f"component_type IN ('{FundingComponentType.TUITION.value}', '{FundingComponentType.MANDATORY_FEES.value}', '{FundingComponentType.ROOM.value}', '{FundingComponentType.MEALS.value}', '{FundingComponentType.HEALTH_INSURANCE.value}', '{FundingComponentType.BOOKS.value}', '{FundingComponentType.TRAVEL.value}', '{FundingComponentType.VISA_SUPPORT.value}', '{FundingComponentType.LIVING_EXPENSES.value}', '{FundingComponentType.STIPEND.value}', '{FundingComponentType.OTHER.value}')"
        ),
        nullable=False,
    )
    amount_min = Column(Float, nullable=True)
    amount_max = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    amount_period = Column(
        String(30),
        CheckConstraint(
            f"amount_period IN ('{AmountPeriod.ANNUAL.value}', '{AmountPeriod.TOTAL.value}', '{AmountPeriod.ONE_TIME.value}', '{AmountPeriod.UNKNOWN.value}')"
        ),
        nullable=False,
        default=AmountPeriod.ANNUAL.value,
    )
    percentage_tuition = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    source_evidence_snippet = Column(Text, nullable=True)

    # Relationships
    award = relationship("Award", back_populates="funding_components")
