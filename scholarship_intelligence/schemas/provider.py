"""Pydantic schemas for scholarship providers / foundations."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProviderBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    provider_type: str = Field(..., description="e.g. UNIVERSITY, FOUNDATION, GOVERNMENT, CORPORATE")
    website_url: Optional[str] = None
    country: str = Field("US", min_length=2, max_length=3)
    description: Optional[str] = None


class ProviderCreate(ProviderBase):
    pass


class ProviderRead(ProviderBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
