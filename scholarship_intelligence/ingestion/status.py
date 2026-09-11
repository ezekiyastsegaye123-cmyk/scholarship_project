"""Status categorization for Phase 1B polite HTTP ingestion."""
from enum import Enum
from typing import Optional, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class FetchStatusCategory(str, Enum):
    """Categorized outcomes for HTTP retrieval operations."""
    SUCCESS = "SUCCESS"
    DNS_ERROR = "DNS_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT = "TIMEOUT"
    HTTP_403 = "HTTP_403"
    HTTP_404 = "HTTP_404"
    HTTP_429 = "HTTP_429"
    HTTP_5XX = "HTTP_5XX"
    OTHER_HTTP_ERROR = "OTHER_HTTP_ERROR"
    INVALID_CONTENT = "INVALID_CONTENT"


class FetchResult(BaseModel):
    """Structured result of an HTTP ingestion attempt."""
    url: str
    status_category: FetchStatusCategory
    http_status: Optional[int] = None
    content: Optional[str] = None
    content_sha256: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    headers: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None
    content_bytes_length: int = 0
    redirect_chain: list[str] = Field(default_factory=list)
    retrieval_duration_seconds: float = 0.0
