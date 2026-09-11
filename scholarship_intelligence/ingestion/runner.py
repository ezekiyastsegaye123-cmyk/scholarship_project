"""Ingestion Pipeline Runner.

Coordinates polite HTTP fetching, HTML extraction, candidate normalization,
and evidence staging without modifying verified canonical records.
"""
import logging
from typing import Optional

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.extractor import HtmlExtractor
from scholarship_intelligence.ingestion.normalizer import CandidateNormalizer
from scholarship_intelligence.ingestion.status import FetchResult, FetchStatusCategory
from scholarship_intelligence.schemas.candidate import CandidateStagingResult

logger = logging.getLogger("scholarship_intelligence.ingestion")


class IngestionRunner:
    """Orchestrates Phase 1B ingestion pipeline."""

    def __init__(
        self,
        http_client: Optional[PoliteHttpClient] = None,
        extractor: Optional[HtmlExtractor] = None,
        normalizer: Optional[CandidateNormalizer] = None,
    ):
        self.http_client = http_client or PoliteHttpClient()
        self.extractor = extractor or HtmlExtractor()
        self.normalizer = normalizer or CandidateNormalizer()

    def ingest_url(
        self,
        url: str,
        authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY,
        academic_cycle: str = "2026-2027",
    ) -> CandidateStagingResult:
        """Fetches a URL and processes it through extraction and normalization."""
        logger.info(f"Ingestion started for URL: {url} (Tier: {authority_tier.value})")

        fetch_res = self.http_client.fetch(url, authority_tier=authority_tier)

        if fetch_res.status_category != FetchStatusCategory.SUCCESS or not fetch_res.content:
            logger.warning(
                f"Fetch incomplete for {url}: status={fetch_res.status_category.value}, "
                f"http_code={fetch_res.http_status}, error={fetch_res.error_message}"
            )
            return CandidateStagingResult(
                fetch_result=fetch_res,
                candidate=None,
                evidence_items=[],
                warnings=[f"Fetch failed with status {fetch_res.status_category.value}: {fetch_res.error_message}"],
            )

        return self.ingest_html(
            html=fetch_res.content,
            source_url=url,
            authority_tier=authority_tier,
            academic_cycle=academic_cycle,
            fetch_result=fetch_res,
        )

    def ingest_html(
        self,
        html: str,
        source_url: str,
        authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY,
        academic_cycle: str = "2026-2027",
        fetch_result: Optional[FetchResult] = None,
    ) -> CandidateStagingResult:
        """Processes raw HTML content directly (useful for tests and offline fixtures)."""
        if fetch_result is None:
            sha = PoliteHttpClient.compute_sha256(html.encode("utf-8"))
            fetch_result = FetchResult(
                url=source_url,
                status_category=FetchStatusCategory.SUCCESS,
                http_status=200,
                content=html,
                content_sha256=sha,
                content_bytes_length=len(html.encode("utf-8")),
            )

        logger.info(f"Extracting structured DOM from {source_url}")
        extracted_page = self.extractor.extract(html, default_title="Candidate Scholarship")

        logger.info(f"Normalizing candidate facts from {source_url}")
        candidate = self.normalizer.normalize(
            extracted=extracted_page,
            fetch_result=fetch_result,
            authority_tier=authority_tier,
            academic_cycle=academic_cycle,
        )

        warnings = []
        if candidate is None:
            warnings.append("No extractable facts with supporting evidence found; candidate staging omitted.")
            return CandidateStagingResult(
                fetch_result=fetch_result,
                candidate=None,
                evidence_items=[],
                warnings=warnings,
            )

        if not candidate.award:
            warnings.append("No explicit award or funding amount could be extracted from page content.")
        if not candidate.deadlines:
            warnings.append("No explicit deadlines identified in page content.")

        logger.info(
            f"Ingestion completed for {source_url}: title='{candidate.title}', "
            f"evidence_items={len(candidate.source_evidence)}, warnings={len(warnings)}"
        )

        return CandidateStagingResult(
            fetch_result=fetch_result,
            candidate=candidate,
            evidence_items=candidate.source_evidence,
            warnings=warnings,
        )
