"""Pydantic schemas for student profile.

Strict Privacy-by-Design & Data Minimization:
- No passwords, SSNs, national ID card scans, or banking credentials.
- No profile vectors, embeddings, or recommendation match scores (deferred).
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


FORBIDDEN_PRIVACY_FIELDS = {
    "password",
    "password_hash",
    "ssn",
    "social_security_number",
    "bank_account",
    "bank_routing",
    "credit_card",
    "cvv",
    "tax_return_pdf",
    "national_id",
    "passport_scan",
    "profile_vector",
    "embedding",
}


class StudentProfileBase(BaseModel):
    # Required basic fields
    citizenship_country: str = Field(..., min_length=2, max_length=3, description="ISO-3166 alpha-2 or alpha-3 code")
    residence_country: str = Field(..., min_length=2, max_length=3)
    intended_degree_level: str = Field("BACHELOR", description="MVP is strictly scoped to BACHELOR")
    intended_destination_country: str = Field("US", description="MVP is strictly scoped to US")
    
    # Recommended academic fields
    gpa: Optional[float] = Field(None, ge=0.0, le=100.0)
    gpa_scale: Optional[float] = Field(4.0, ge=1.0, le=100.0)
    
    # Optional fields
    intended_major: Optional[str] = None
    english_test_type: Optional[str] = Field(None, description="e.g. TOEFL, IELTS, DUOLINGO, NONE")
    english_test_score: Optional[float] = None
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    act_score: Optional[int] = Field(None, ge=1, le=36)
    
    # Broad self-reported financial tier (sensitive category, broad tier only)
    financial_need_tier: Optional[str] = Field(
        None,
        description="Broad category: HIGH, MODERATE, LOW, NONE. No financial documents or bank data."
    )
    
    # Qualitative contextual criteria
    academic_achievements: List[str] = Field(default_factory=list)
    extracurricular_activities: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_privacy_fields(cls, data: any) -> any:
        if isinstance(data, dict):
            for forbidden in FORBIDDEN_PRIVACY_FIELDS:
                if forbidden in data:
                    raise ValueError(f"Privacy violation: field '{forbidden}' is strictly forbidden in StudentProfile")
        return data


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileRead(StudentProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
