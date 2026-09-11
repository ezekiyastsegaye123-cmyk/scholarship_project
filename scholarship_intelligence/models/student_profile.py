"""SQLAlchemy model for StudentProfile.

Strict Privacy-by-Design & Data Minimization:
- No passwords, SSNs, national ID card scans, or banking credentials.
- No profile vectors, embeddings, or recommendation match scores (deferred).
- Uses portable JSON columns for structured lists.
"""
from sqlalchemy import Column, Float, Integer, JSON, String

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Required core demographic fields
    citizenship_country = Column(String(3), nullable=False, index=True)
    residence_country = Column(String(3), nullable=False)
    intended_degree_level = Column(String(50), nullable=False, default="BACHELOR")
    intended_destination_country = Column(String(3), nullable=False, default="US")

    # Recommended academic metrics
    gpa = Column(Float, nullable=True)
    gpa_scale = Column(Float, nullable=True, default=4.0)

    # Optional testing & preferences
    intended_major = Column(String(255), nullable=True)
    english_test_type = Column(String(50), nullable=True)
    english_test_score = Column(Float, nullable=True)
    sat_score = Column(Integer, nullable=True)
    act_score = Column(Integer, nullable=True)

    # Broad self-reported financial tier (sensitive category, broad tier only)
    financial_need_tier = Column(String(50), nullable=True)

    # Portable JSON collections for qualitative background
    academic_achievements = Column(JSON, nullable=False, default=list)
    extracurricular_activities = Column(JSON, nullable=False, default=list)
    interests = Column(JSON, nullable=False, default=list)
