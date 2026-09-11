"""SQLAlchemy model for application preparation requirements."""
from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import RequirementKind, RequirementType
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class ApplicationRequirement(Base, TimestampMixin):
    __tablename__ = "application_requirements"

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
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    submission_format = Column(String(100), nullable=True)
    source_evidence_snippet = Column(Text, nullable=True)

    # Relationships
    opportunity = relationship("ScholarshipOpportunity", back_populates="application_requirements")
