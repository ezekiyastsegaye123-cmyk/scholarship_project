"""Pydantic schemas for funding awards and decomposed components."""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import AmountPeriod, FundingClassification, FundingComponentType, TriState


class FundingComponentBase(BaseModel):
    component_type: FundingComponentType
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    currency: str = Field("USD", min_length=3, max_length=3)
    amount_period: AmountPeriod = Field(default=AmountPeriod.ANNUAL)
    percentage_tuition: Optional[float] = None
    description: Optional[str] = None
    source_evidence_snippet: Optional[str] = None


class FundingComponentCreate(FundingComponentBase):
    pass


class FundingComponentRead(FundingComponentBase):
    id: str
    award_id: str
    model_config = ConfigDict(from_attributes=True)


class AwardBase(BaseModel):
    funding_classification: FundingClassification = Field(default=FundingClassification.UNKNOWN)
    title: str = Field(..., min_length=2, max_length=255)
    is_renewable: TriState = Field(default=TriState.UNKNOWN)
    renewal_criteria: Optional[str] = None
    estimated_annual_value_usd: Optional[float] = None
    funding_components: List[FundingComponentCreate] = Field(default_factory=list)


class AwardCreate(AwardBase):
    pass


class AwardRead(AwardBase):
    id: str
    scholarship_id: str
    funding_components: List[FundingComponentRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
