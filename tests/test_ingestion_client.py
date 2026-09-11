"""Automated tests for PoliteHttpClient and HTTP status categorization."""
import httpx
import pytest

from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.status import FetchStatusCategory


def test_fetch_success():
    """Verifies successful HTTP 200 response handling and SHA-256 computation."""
    html = "<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text=html,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

    transport = httpx.MockTransport(handler)
    client = PoliteHttpClient(transport=transport)
    res = client.fetch("https://university.edu/scholarship")

    assert res.status_category == FetchStatusCategory.SUCCESS
    assert res.http_status == 200
    assert res.content == html
    assert res.content_sha256 == PoliteHttpClient.compute_sha256(html.encode("utf-8"))
    assert res.content_bytes_length == len(html.encode("utf-8"))


def test_fetch_403_forbidden():
    """Verifies HTTP 403 bot challenge is cleanly recorded without retry looping."""
    transport = httpx.MockTransport(lambda req: httpx.Response(status_code=403, text="Forbidden"))
    client = PoliteHttpClient(transport=transport)
    res = client.fetch("https://university.edu/protected")

    assert res.status_category == FetchStatusCategory.HTTP_403
    assert res.http_status == 403
    assert "forbidden" in res.error_message.lower()


def test_fetch_404_not_found():
    """Verifies HTTP 404 dead link categorization."""
    transport = httpx.MockTransport(lambda req: httpx.Response(status_code=404, text="Not Found"))
    client = PoliteHttpClient(transport=transport)
    res = client.fetch("https://university.edu/dead-link")

    assert res.status_category == FetchStatusCategory.HTTP_404
    assert res.http_status == 404


def test_fetch_429_rate_limited():
    """Verifies HTTP 429 rate limit categorization."""
    transport = httpx.MockTransport(lambda req: httpx.Response(status_code=429, text="Too Many Requests"))
    client = PoliteHttpClient(transport=transport)
    res = client.fetch("https://university.edu/rate-limited")

    assert res.status_category == FetchStatusCategory.HTTP_429
    assert res.http_status == 429


def test_fetch_5xx_retries_and_exponential_backoff():
    """Verifies 5xx errors trigger bounded retries with backoff."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(status_code=503, text="Service Unavailable")

    transport = httpx.MockTransport(handler)
    client = PoliteHttpClient(transport=transport, max_retries=2, backoff_factor=0.01)
    res = client.fetch("https://university.edu/transient-error")

    # Initial attempt + 2 retries = 3 total attempts
    assert attempt_count == 3
    assert res.status_category == FetchStatusCategory.HTTP_5XX
    assert res.http_status == 503


def test_fetch_timeout():
    """Verifies timeout exception triggers bounded retry and returns TIMEOUT status."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        raise httpx.ReadTimeout("Read timed out")

    transport = httpx.MockTransport(handler)
    client = PoliteHttpClient(transport=transport, max_retries=1, backoff_factor=0.01)
    res = client.fetch("https://university.edu/slow-page")

    assert attempt_count == 2
    assert res.status_category == FetchStatusCategory.TIMEOUT
    assert "timed out" in res.error_message.lower()


def test_fetch_oversized_response():
    """Verifies response size limit protects against giant downloads."""
    huge_text = "A" * (200 * 1024)  # 200 KB
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            status_code=200,
            text=huge_text,
            headers={"Content-Length": str(len(huge_text)), "Content-Type": "text/html"},
        )
    )
    # Set limit to 50 KB
    client = PoliteHttpClient(transport=transport, max_response_bytes=50 * 1024)
    res = client.fetch("https://university.edu/large-file")

    assert res.status_category == FetchStatusCategory.INVALID_CONTENT
    assert "exceeds limit" in res.error_message.lower()


def test_fetch_invalid_content_type():
    """Verifies binary or unexpected Content-Type is rejected."""
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            status_code=200,
            content=b"%PDF-1.4...",
            headers={"Content-Type": "application/pdf"},
        )
    )
    client = PoliteHttpClient(transport=transport)
    res = client.fetch("https://university.edu/brochure.pdf")

    assert res.status_category == FetchStatusCategory.INVALID_CONTENT
    assert "Unsupported Content-Type" in res.error_message
