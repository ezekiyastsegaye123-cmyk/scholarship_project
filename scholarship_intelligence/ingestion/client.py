"""Polite HTTP Ingestion Client using HTTPX.

Implements conservative crawling, strict timeouts, bounded retries with exponential backoff,
response size limits, and robust status categorization.
"""
import hashlib
import time
from typing import Optional, Dict
import httpx

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.ingestion.safety import (
    IngestionSafetyError,
    is_safe_content_type,
    validate_url,
)
from scholarship_intelligence.ingestion.status import FetchResult, FetchStatusCategory

DEFAULT_USER_AGENT = (
    "ScholarshipDiscoveryEngine/1.0 (+https://github.com/ezekiyastsegaye123-cmyk/scholarship_project; "
    "verification-contact: verification@scholarship-engine.local)"
)
DEFAULT_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 10.0
DEFAULT_WRITE_TIMEOUT = 5.0
DEFAULT_POOL_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5


class PoliteHttpClient:
    """Polite HTTP client tailored for academic and institutional webpage ingestion."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        write_timeout: float = DEFAULT_WRITE_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        delay_between_requests: float = 0.0,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        self.user_agent = user_agent
        self.max_response_bytes = max_response_bytes
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay_between_requests = delay_between_requests
        self._last_request_time: float = 0.0
        self.transport = transport

    def _apply_polite_delay(self) -> None:
        """Enforces polite rate limiting delay between consecutive requests."""
        if self.delay_between_requests > 0 and self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay_between_requests:
                time.sleep(self.delay_between_requests - elapsed)
        self._last_request_time = time.time()

    @staticmethod
    def compute_sha256(content_bytes: bytes) -> str:
        """Computes deterministic SHA-256 digest of response bytes."""
        return hashlib.sha256(content_bytes).hexdigest()

    def fetch(
        self,
        url: str,
        authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY,
    ) -> FetchResult:
        """Fetches URL with polite constraints, retries, and error categorization."""
        try:
            validate_url(url)
        except IngestionSafetyError as err:
            return FetchResult(
                url=url,
                status_category=FetchStatusCategory.INVALID_CONTENT,
                error_message=f"Safety validation failed: {err}",
            )

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
            "Accept-Language": "en-US,en;q=0.8",
        }

        timeout = httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=self.write_timeout,
            pool=DEFAULT_POOL_TIMEOUT,
        )

        attempts = 0
        last_error_message = None

        while attempts <= self.max_retries:
            self._apply_polite_delay()
            attempts += 1

            try:
                with httpx.Client(
                    timeout=timeout,
                    transport=self.transport,
                    follow_redirects=True,
                    max_redirects=5,
                ) as client:
                    response = client.get(url, headers=headers)

                    # Response-size protection: check Content-Length header if present
                    cl_header = response.headers.get("content-length")
                    if cl_header and cl_header.isdigit() and int(cl_header) > self.max_response_bytes:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.INVALID_CONTENT,
                            http_status=response.status_code,
                            error_message=(
                                f"Response Content-Length ({cl_header} bytes) exceeds "
                                f"limit of {self.max_response_bytes} bytes."
                            ),
                            headers=dict(response.headers),
                        )

                    raw_bytes = response.content
                    if len(raw_bytes) > self.max_response_bytes:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.INVALID_CONTENT,
                            http_status=response.status_code,
                            error_message=(
                                f"Response size ({len(raw_bytes)} bytes) exceeds "
                                f"limit of {self.max_response_bytes} bytes."
                            ),
                            headers=dict(response.headers),
                        )

                    # Content-type verification
                    content_type = response.headers.get("content-type", "")
                    if not is_safe_content_type(content_type):
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.INVALID_CONTENT,
                            http_status=response.status_code,
                            error_message=f"Unsupported Content-Type: '{content_type}'",
                            headers=dict(response.headers),
                        )

                    status_code = response.status_code
                    content_sha = self.compute_sha256(raw_bytes)

                    # Status categorization
                    if status_code == 200:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.SUCCESS,
                            http_status=200,
                            content=response.text,
                            content_sha256=content_sha,
                            headers=dict(response.headers),
                            content_bytes_length=len(raw_bytes),
                        )
                    elif status_code == 403:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.HTTP_403,
                            http_status=403,
                            error_message="Access forbidden (HTTP 403 bot challenge or permission denied).",
                            headers=dict(response.headers),
                        )
                    elif status_code == 404:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.HTTP_404,
                            http_status=404,
                            error_message="Resource not found (HTTP 404 dead link).",
                            headers=dict(response.headers),
                        )
                    elif status_code == 429:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.HTTP_429,
                            http_status=429,
                            error_message="Rate limit exceeded (HTTP 429).",
                            headers=dict(response.headers),
                        )
                    elif 500 <= status_code <= 599:
                        last_error_message = f"Server error (HTTP {status_code})."
                        if attempts <= self.max_retries:
                            backoff = self.backoff_factor * (2 ** (attempts - 1))
                            time.sleep(backoff)
                            continue
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.HTTP_5XX,
                            http_status=status_code,
                            error_message=last_error_message,
                            headers=dict(response.headers),
                        )
                    else:
                        return FetchResult(
                            url=url,
                            status_category=FetchStatusCategory.OTHER_HTTP_ERROR,
                            http_status=status_code,
                            error_message=f"Unexpected HTTP status {status_code}.",
                            headers=dict(response.headers),
                        )

            except httpx.TimeoutException as exc:
                last_error_message = f"Request timed out: {exc}"
                if attempts <= self.max_retries:
                    backoff = self.backoff_factor * (2 ** (attempts - 1))
                    time.sleep(backoff)
                    continue
                return FetchResult(
                    url=url,
                    status_category=FetchStatusCategory.TIMEOUT,
                    error_message=last_error_message,
                )

            except httpx.ConnectError as exc:
                exc_str = str(exc).lower()
                last_error_message = f"Connection failed: {exc}"
                is_dns = "name or service not known" in exc_str or "getaddrinfo failed" in exc_str
                if attempts <= self.max_retries and not is_dns:
                    backoff = self.backoff_factor * (2 ** (attempts - 1))
                    time.sleep(backoff)
                    continue
                category = FetchStatusCategory.DNS_ERROR if is_dns else FetchStatusCategory.CONNECTION_ERROR
                return FetchResult(
                    url=url,
                    status_category=category,
                    error_message=last_error_message,
                )

            except Exception as exc:
                return FetchResult(
                    url=url,
                    status_category=FetchStatusCategory.CONNECTION_ERROR,
                    error_message=f"Unhandled request exception: {exc}",
                )

        return FetchResult(
            url=url,
            status_category=FetchStatusCategory.TIMEOUT,
            error_message=last_error_message or "Maximum retries exhausted.",
        )
