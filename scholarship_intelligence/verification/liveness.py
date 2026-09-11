"""Source liveness checker, redirect tracking, and soft-404 detection."""
from datetime import datetime, timezone
import hashlib
from typing import List, Optional
import httpx

from scholarship_intelligence.domain.enums import LivenessStatus
from scholarship_intelligence.schemas.verification import SourceLivenessResult

SOFT_404_INDICATORS = [
    "page not found",
    "error 404",
    "404 not found",
    "404 error",
    "page could not be found",
    "the page you requested could not be found",
    "the requested url was not found",
    "opportunity has been discontinued",
    "this scholarship has been discontinued",
    "scholarship has expired and is no longer available",
    "this scholarship is no longer active",
    "program has ended",
    "this page does not exist",
    "we couldn't find that page",
    "we can't find the page you're looking for",
]


class SourceLivenessChecker:
    """Performs deterministic HTTP liveness sweeps, redirect chain tracking, and soft-404 inspection."""

    def __init__(self, max_redirects: int = 5, timeout_seconds: float = 10.0, user_agent: Optional[str] = None):
        self.max_redirects = max_redirects
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent or "ScholarshipIntelligence/1.0 (Verification Crawler; +https://example.org/bot)"

    def check_liveness(
        self,
        url: str,
        client: Optional[httpx.Client] = None,
    ) -> SourceLivenessResult:
        """Executes a liveness check against the target URL.
        
        Preserves complete redirect chains, content hashes, and identifies soft-404s.
        Historical evidence is never modified or erased by this check.
        """
        redirect_chain: List[str] = []
        checked_at = datetime.now(timezone.utc)

        # If external client not provided, use an ephemeral client
        should_close = False
        if client is None:
            client = httpx.Client(
                timeout=httpx.Timeout(self.timeout_seconds),
                headers={"User-Agent": self.user_agent},
                follow_redirects=False,
            )
            should_close = True

        current_url = url
        redirect_count = 0
        response = None

        try:
            while redirect_count <= self.max_redirects:
                try:
                    response = client.get(current_url)
                except httpx.TimeoutException as exc:
                    return SourceLivenessResult(
                        source_url=url,
                        liveness_status=LivenessStatus.TIMEOUT,
                        http_status=None,
                        final_url=current_url,
                        redirect_chain=redirect_chain,
                        error_message=f"Request timed out: {exc}",
                        is_live=False,
                        checked_at=checked_at,
                    )
                except (httpx.ConnectError, httpx.NetworkError, httpx.ProtocolError) as exc:
                    return SourceLivenessResult(
                        source_url=url,
                        liveness_status=LivenessStatus.UNAVAILABLE,
                        http_status=None,
                        final_url=current_url,
                        redirect_chain=redirect_chain,
                        error_message=f"Network connection failure: {exc}",
                        is_live=False,
                        checked_at=checked_at,
                    )

                # Check for redirects
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_chain.append(current_url)
                    location = response.headers.get("Location")
                    if not location:
                        break
                    # Resolve relative redirect URLs
                    current_url = str(httpx.URL(current_url).join(location))
                    redirect_count += 1
                    if redirect_count > self.max_redirects:
                        return SourceLivenessResult(
                            source_url=url,
                            liveness_status=LivenessStatus.REDIRECTED,
                            http_status=response.status_code,
                            final_url=current_url,
                            redirect_chain=redirect_chain,
                            error_message="Exceeded maximum redirect limit (5).",
                            is_live=False,
                            checked_at=checked_at,
                        )
                    continue
                else:
                    # Final non-redirect response reached
                    break

            final_status = response.status_code if response else None
            final_url = current_url
            raw_content = response.content if response else b""
            content_type = response.headers.get("Content-Type", "") if response else ""
            content_sha256 = hashlib.sha256(raw_content).hexdigest() if raw_content else None

            # Categorize HTTP status
            if final_status == 200:
                # Inspect for soft-404 in HTML content
                text_lower = response.text.lower() if response else ""
                is_soft_404 = any(phrase in text_lower for phrase in SOFT_404_INDICATORS)
                if is_soft_404:
                    return SourceLivenessResult(
                        source_url=url,
                        liveness_status=LivenessStatus.NOT_FOUND,
                        http_status=200,
                        final_url=final_url,
                        redirect_chain=redirect_chain,
                        content_sha256=content_sha256,
                        content_type=content_type,
                        error_message="Soft-404 detected: page returns HTTP 200 but contains definitive missing/discontinued indicator.",
                        is_live=False,
                        is_soft_404=True,
                        checked_at=checked_at,
                    )
                
                # Check for redirected vs live
                status = LivenessStatus.REDIRECTED if len(redirect_chain) > 0 else LivenessStatus.LIVE
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=status,
                    http_status=200,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    is_live=True,
                    is_soft_404=False,
                    checked_at=checked_at,
                )
            elif final_status in (404, 410):
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=LivenessStatus.NOT_FOUND,
                    http_status=final_status,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    error_message=f"HTTP {final_status} Resource Not Found",
                    is_live=False,
                    checked_at=checked_at,
                )
            elif final_status == 403:
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=LivenessStatus.FORBIDDEN,
                    http_status=403,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    error_message="HTTP 403 Access Forbidden",
                    is_live=False,
                    checked_at=checked_at,
                )
            elif final_status == 429:
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=LivenessStatus.RATE_LIMITED,
                    http_status=429,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    error_message="HTTP 429 Rate Limited",
                    is_live=False,
                    checked_at=checked_at,
                )
            elif final_status and final_status >= 500:
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=LivenessStatus.SERVER_ERROR,
                    http_status=final_status,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    error_message=f"HTTP {final_status} Internal Server Error",
                    is_live=False,
                    checked_at=checked_at,
                )
            else:
                return SourceLivenessResult(
                    source_url=url,
                    liveness_status=LivenessStatus.UNAVAILABLE,
                    http_status=final_status,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    content_sha256=content_sha256,
                    content_type=content_type,
                    error_message=f"Unexpected HTTP status: {final_status}",
                    is_live=False,
                    checked_at=checked_at,
                )
        finally:
            if should_close:
                client.close()
