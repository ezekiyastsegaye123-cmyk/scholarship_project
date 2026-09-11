"""URL and response safety validations for polite ingestion."""
import urllib.parse
from typing import Optional


class IngestionSafetyError(ValueError):
    """Raised when an ingestion URL or response violates safety constraints."""
    pass


ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048
ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
}


def validate_url(url: str) -> None:
    """Validates URL for safe HTTP ingestion.
    
    Raises IngestionSafetyError if the URL is invalid or unsafe.
    """
    if not url or not isinstance(url, str):
        raise IngestionSafetyError("URL must be a non-empty string.")

    if len(url) > MAX_URL_LENGTH:
        raise IngestionSafetyError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters.")

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise IngestionSafetyError(f"Malformed URL: {e}") from e

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise IngestionSafetyError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted."
        )

    if not parsed.netloc:
        raise IngestionSafetyError("URL missing valid network location / domain.")


def is_safe_content_type(content_type_header: Optional[str]) -> bool:
    """Checks if the Content-Type header indicates safe HTML or text content."""
    if not content_type_header:
        # If server omits Content-Type, allow HTML sniffing in client
        return True

    mime_part = content_type_header.split(";")[0].strip().lower()
    return mime_part in ALLOWED_CONTENT_TYPES
