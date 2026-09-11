"""Pydantic schemas for sources and provenance tracking."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import AuthorityTier


class OfficialSourceBase(BaseModel):
    url: str = Field(..., min_length=5, max_length=1000)
    source_domain: str = Field(..., min_length=3, max_length=255)
    authority_tier: AuthorityTier = Field(default=AuthorityTier.OFFICIAL_UNIVERSITY)
    is_primary: bool = True
    page_title: Optional[str] = None
    extracted_text_snippet: Optional[str] = None
    last_crawled_at: Optional[datetime] = None
    last_http_status: Optional[int] = None


class OfficialSourceCreate(OfficialSourceBase):
    pass


class OfficialSourceRead(OfficialSourceBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)


class DiscoverySourceBase(BaseModel):
    url: str = Field(..., min_length=5, max_length=1000)
    source_name: str = Field(..., min_length=2, max_length=255)
    authority_tier: AuthorityTier = Field(default=AuthorityTier.DISCOVERY_AGGREGATOR)
    discovery_notes: Optional[str] = None
    discovered_at: Optional[datetime] = None


class DiscoverySourceCreate(DiscoverySourceBase):
    pass


class DiscoverySourceRead(DiscoverySourceBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)
