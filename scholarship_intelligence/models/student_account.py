"""SQLAlchemy model for StudentAccount.

Manages student identity and authentication credentials:
- Salted scrypt password hash.
- Unique normalized email address.
- Relationships to profile, saved opportunities, applications, and comparisons.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class StudentAccount(Base, TimestampMixin):
    __tablename__ = "student_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships - strictly owned by the student
    profile = relationship("StudentProfile", back_populates="account", uselist=False, cascade="all, delete-orphan")
    saved_opportunities = relationship("SavedOpportunity", back_populates="account", cascade="all, delete-orphan")
    applications = relationship("ApplicationRecord", back_populates="account", cascade="all, delete-orphan")
    comparison_selections = relationship("ComparisonSelection", back_populates="account", cascade="all, delete-orphan")
