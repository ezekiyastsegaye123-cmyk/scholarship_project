"""Tests for source liveness inspection, redirect tracking, and soft-404 detection."""
import httpx
import pytest

from scholarship_intelligence.domain.enums import LivenessStatus
from scholarship_intelligence.verification.liveness import SourceLivenessChecker


def test_liveness_http_200_live():
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(200, text="<html><body>Welcome to Official Financial Aid</body></html>"))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://clarku.edu/finaid", client=client)
    assert res.is_live is True
    assert res.is_soft_404 is False
    assert res.liveness_status == LivenessStatus.LIVE
    assert res.http_status == 200
    assert res.content_sha256 is not None


def test_liveness_redirect_chain_tracking():
    checker = SourceLivenessChecker(max_redirects=5)

    def handler(req):
        if req.url.path == "/old-aid":
            return httpx.Response(301, headers={"Location": "https://clarku.edu/new-aid"})
        elif req.url.path == "/new-aid":
            return httpx.Response(200, text="<html><body>New Aid Page</body></html>")
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://clarku.edu/old-aid", client=client)
    assert res.is_live is True
    assert res.liveness_status == LivenessStatus.REDIRECTED
    assert res.final_url == "https://clarku.edu/new-aid"
    assert len(res.redirect_chain) == 1
    assert "https://clarku.edu/old-aid" in res.redirect_chain


def test_liveness_soft_404_detection():
    checker = SourceLivenessChecker()
    # Server returns 200 OK, but page body clearly says the opportunity is discontinued or not found
    soft_404_html = "<html><body><h1>Page Not Found</h1><p>Sorry, this scholarship has been discontinued.</p></body></html>"
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(200, text=soft_404_html))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/old-award", client=client)
    assert res.is_live is False
    assert res.is_soft_404 is True
    assert res.liveness_status == LivenessStatus.NOT_FOUND
    assert "Soft-404 detected" in res.error_message


def test_liveness_http_404_not_found():
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(404, text="Not Found"))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/dead-link", client=client)
    assert res.is_live is False
    assert res.liveness_status == LivenessStatus.NOT_FOUND
    assert res.http_status == 404


def test_liveness_http_403_forbidden():
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(403, text="Forbidden"))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/secure", client=client)
    assert res.is_live is False
    assert res.liveness_status == LivenessStatus.FORBIDDEN
    assert res.http_status == 403


def test_liveness_http_429_rate_limited():
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(429, text="Too Many Requests"))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/rate-limit", client=client)
    assert res.is_live is False
    assert res.liveness_status == LivenessStatus.RATE_LIMITED
    assert res.http_status == 429


def test_liveness_http_500_server_error():
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(500, text="Internal Server Error"))
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/server-err", client=client)
    assert res.is_live is False
    assert res.liveness_status == LivenessStatus.SERVER_ERROR
    assert res.http_status == 500


def test_liveness_timeout():
    checker = SourceLivenessChecker()

    def timeout_handler(req):
        raise httpx.ReadTimeout("Connection timed out")

    mock_transport = httpx.MockTransport(timeout_handler)
    client = httpx.Client(transport=mock_transport)

    res = checker.check_liveness("https://university.edu/slow", client=client)
    assert res.is_live is False
    assert res.liveness_status == LivenessStatus.TIMEOUT


def test_liveness_preserves_evidence_when_source_becomes_404():
    """Mandatory test: A 404 does not alter or erase historical evidence records."""
    historical_evidence_text = "Harvard provides 100% need-based aid to all undergraduates regardless of citizenship."
    historical_hash = "abcdef1234567890"
    
    # Source is now returning 404
    checker = SourceLivenessChecker()
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(404, text="Page Deleted"))
    client = httpx.Client(transport=mock_transport)

    liveness_res = checker.check_liveness("https://college.harvard.edu/dead", client=client)
    assert liveness_res.liveness_status == LivenessStatus.NOT_FOUND

    # Assert historical evidence remains intact and unmutated
    assert historical_evidence_text == "Harvard provides 100% need-based aid to all undergraduates regardless of citizenship."
    assert historical_hash == "abcdef1234567890"
