"""Pydantic schemas for higher education institutions offering undergraduate programs."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import NeedPolicy


class UniversityBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    country: str = Field("US", min_length=2, max_length=3)
    admissions_need_policy: NeedPolicy = Field(
        default=NeedPolicy.UNKNOWN,
        description="Institutional policy for international undergraduate applicants"
    )
    official_admissions_url: Optional[str] = None
    official_financial_aid_url: Optional[str] = None


class UniversityCreate(UniversityBase):
    pass


class UniversityRead(UniversityBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
