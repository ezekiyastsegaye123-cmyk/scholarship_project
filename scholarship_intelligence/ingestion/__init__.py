"""Phase 1B Ingestion and Normalization Layer."""
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.extractor import HtmlExtractor, ExtractedPage, ExtractedTable, ExtractedSection
from scholarship_intelligence.ingestion.normalizer import CandidateNormalizer
from scholarship_intelligence.ingestion.runner import IngestionRunner
from scholarship_intelligence.ingestion.safety import IngestionSafetyError, validate_url, is_safe_content_type
from scholarship_intelligence.ingestion.status import FetchResult, FetchStatusCategory

__all__ = [
    "PoliteHttpClient",
    "HtmlExtractor",
    "ExtractedPage",
    "ExtractedTable",
    "ExtractedSection",
    "CandidateNormalizer",
    "IngestionRunner",
    "IngestionSafetyError",
    "validate_url",
    "is_safe_content_type",
    "FetchResult",
    "FetchStatusCategory",
]
