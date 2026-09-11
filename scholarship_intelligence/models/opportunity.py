"""SQLAlchemy model for ScholarshipOpportunity."""
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from scholarship_intelligence.domain.enums import TriState, VerificationState
from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class ScholarshipOpportunity(Base, TimestampMixin):
    __tablename__ = "scholarship_opportunities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider_id = Column(String(36), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True)
    university_id = Column(String(36), ForeignKey("universities.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    target_degree_level = Column(String(50), nullable=False, default="BACHELOR")
    destination_country = Column(String(3), nullable=False, default="US")
    academic_cycle = Column(String(20), nullable=False, default="2026-2027")
    varies_by_program = Column(Boolean, nullable=False, default=False)

    # Multi-State semantic fields (CheckConstraint)
    international_students_allowed = Column(
        String(20),
        CheckConstraint(
            f"international_students_allowed IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )
    requires_sat = Column(
        String(20),
        CheckConstraint(
            f"requires_sat IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )
    requires_act = Column(
        String(20),
        CheckConstraint(
            f"requires_act IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )
    requires_css_profile = Column(
        String(20),
        CheckConstraint(
            f"requires_css_profile IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )
    financial_need_required = Column(
        String(20),
        CheckConstraint(
            f"financial_need_required IN ('{TriState.YES.value}', '{TriState.NO.value}', '{TriState.UNKNOWN.value}', '{TriState.NOT_APPLICABLE.value}', '{TriState.CONFLICTING.value}')"
        ),
        nullable=False,
        default=TriState.UNKNOWN.value,
    )

    # Verification state (No arbitrary trust score)
    verification_status = Column(
        String(50),
        CheckConstraint(
            f"verification_status IN ('{VerificationState.VERIFIED.value}', '{VerificationState.PARTIALLY_VERIFIED.value}', '{VerificationState.CONFLICTING.value}', '{VerificationState.OUTDATED.value}', '{VerificationState.UNVERIFIED.value}', '{VerificationState.SOURCE_UNAVAILABLE.value}', '{VerificationState.QUARANTINED_FOR_REVIEW.value}')"
        ),
        nullable=False,
        default=VerificationState.UNVERIFIED.value,
    )

    # Unique deterministic fingerprint for seed idempotency & deduplication
    fingerprint_sha256 = Column(String(64), nullable=False, unique=True, index=True)

    # Relationships
    provider = relationship("Provider", back_populates="opportunities")
    university = relationship("University", back_populates="opportunities")
    official_sources = relationship("OfficialSource", back_populates="opportunity", cascade="all, delete-orphan")
    discovery_sources = relationship("DiscoverySource", back_populates="opportunity", cascade="all, delete-orphan")
    eligibility_rules = relationship("EligibilityRule", back_populates="opportunity", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="opportunity", cascade="all, delete-orphan")
    award = relationship("Award", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    deadlines = relationship("Deadline", back_populates="opportunity", cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="opportunity", cascade="all, delete-orphan")
    conflict_records = relationship("ConflictRecord", back_populates="opportunity", cascade="all, delete-orphan")
    application_requirements = relationship("ApplicationRequirement", back_populates="opportunity", cascade="all, delete-orphan")
    verification_histories = relationship("VerificationHistory", back_populates="opportunity", cascade="all, delete-orphan")
    source_liveness_logs = relationship("SourceLivenessLog", back_populates="opportunity", cascade="all, delete-orphan")

