"""SQLAlchemy models for eligibility rules and opportunity requirements."""
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import RequirementKind, RequirementType, RuleKind
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class EligibilityRule(Base, TimestampMixin):
    __tablename__ = "eligibility_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(100), nullable=False)
    kind = Column(
        String(50),
        CheckConstraint(
            f"kind IN ('{RuleKind.REQUIRED.value}', '{RuleKind.CONDITIONAL.value}', '{RuleKind.PREFERRED.value}', '{RuleKind.UNKNOWN.value}')"
        ),
        nullable=False,
        default=RuleKind.REQUIRED.value,
    )
    expression_json = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    source_evidence_snippet = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="eligibility_rules")


class Requirement(Base, TimestampMixin):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scholarship_id = Column(String(36), ForeignKey("scholarship_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_type = Column(
        String(50),
        CheckConstraint(
            f"requirement_type IN ('{RequirementType.TRANSCRIPT.value}', '{RequirementType.RECOMMENDATION.value}', '{RequirementType.ESSAY.value}', '{RequirementType.STANDARDIZED_TEST.value}', '{RequirementType.ENGLISH_PROFICIENCY.value}', '{RequirementType.CSS_PROFILE.value}', '{RequirementType.ISFAA.value}', '{RequirementType.FINANCIAL_DOCUMENTS.value}', '{RequirementType.PORTFOLIO.value}', '{RequirementType.APPLICATION_FORM.value}', '{RequirementType.INTERVIEW.value}', '{RequirementType.OTHER.value}')"
        ),
        nullable=False,
    )
    kind = Column(
        String(50),
        CheckConstraint(
            f"kind IN ('{RequirementKind.REQUIRED.value}', '{RequirementKind.CONDITIONAL.value}', '{RequirementKind.PREFERRED.value}', '{RequirementKind.UNKNOWN.value}', '{RequirementKind.NOT_APPLICABLE.value}')"
        ),
        nullable=False,
        default=RequirementKind.REQUIRED.value,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_evidence_snippet = Column(Text, nullable=True)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="requirements")
