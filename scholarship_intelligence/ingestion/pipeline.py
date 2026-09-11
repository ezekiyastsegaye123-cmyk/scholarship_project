"""Live Ingestion Pipeline orchestrator.

Coordinates polite source fetching, content hashing, candidate extraction,
granular change detection, multi-source verification, conflict handling,
and transactional promotion to canonical storage.
"""
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from scholarship_intelligence.domain.enums import AuthorityTier, LivenessStatus
from scholarship_intelligence.ingestion.change_detector import ChangeDetector, FactComparisonResult
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.extractor import HtmlExtractor
from scholarship_intelligence.ingestion.normalizer import CandidateNormalizer
from scholarship_intelligence.ingestion.runner import IngestionRunner
from scholarship_intelligence.ingestion.source_registry import SourceRegistry
from scholarship_intelligence.ingestion.status import FetchStatusCategory
from scholarship_intelligence.models.ingestion_run import IngestionRun
from scholarship_intelligence.models.ingestion_source import IngestionSource
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.source import OfficialSource
from scholarship_intelligence.models.source_liveness import SourceLivenessLog
from scholarship_intelligence.schemas.verification import SourceLivenessResult
from scholarship_intelligence.verification.engine import VerificationEngine
from scholarship_intelligence.verification.promoter import CanonicalPromoter

logger = logging.getLogger("scholarship_intelligence.pipeline")


class PipelineRunSummary(BaseModel):
    """Summary metrics of an executed ingestion pipeline run."""
    run_id: str
    run_type: str
    status: str
    sources_attempted: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    opportunities_scanned: int = 0
    opportunities_updated: int = 0
    opportunities_created: int = 0
    conflicts_detected: int = 0
    errors: List[str] = Field(default_factory=list)


class IngestionPipeline:
    """End-to-end live scholarship ingestion and re-verification pipeline."""

    def __init__(
        self,
        runner: Optional[IngestionRunner] = None,
        verification_engine: Optional[VerificationEngine] = None,
    ):
        self.runner = runner or IngestionRunner(
            http_client=PoliteHttpClient(),
            extractor=HtmlExtractor(),
            normalizer=CandidateNormalizer(),
        )
        self.verification_engine = verification_engine or VerificationEngine()

    def run(
        self,
        session: Session,
        sources: Optional[List[IngestionSource]] = None,
        run_type: str = "SCHEDULED",
        force_reverify: bool = False,
        reference_time: Optional[datetime] = None,
    ) -> PipelineRunSummary:
        """Executes a complete ingestion run across registered sources."""
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # 1. Initialize IngestionRun record
        run_record = IngestionRun(
            run_type=run_type,
            status="IN_PROGRESS",
            started_at=now,
            reference_time=now,
        )
        session.add(run_record)
        session.flush()

        # 2. Resolve target sources
        target_sources = sources
        if target_sources is None:
            target_sources = SourceRegistry.get_active_sources(
                session, due_only=False, reference_time=now
            )

        errors: List[str] = []

        for source in target_sources:
            run_record.sources_attempted += 1
            source_tier = AuthorityTier(source.authority_tier) if source.authority_tier in AuthorityTier._value2member_map_ else AuthorityTier.THIRD_PARTY

            previous_content_hash = source.last_content_sha256

            # Execute safe HTTP fetch
            fetch_res = self.runner.http_client.fetch(source.url, authority_tier=source_tier)
            success = (fetch_res.status_category == FetchStatusCategory.SUCCESS and bool(fetch_res.content))

            # Record crawl outcome in registry
            SourceRegistry.record_crawl_result(
                db=session,
                source_id=source.id,
                http_status=fetch_res.http_status or 0,
                content_sha256=fetch_res.content_sha256,
                crawled_at=now,
                success=success,
            )

            # Locate existing canonical opportunity associated with this source URL if any
            existing_source_record = (
                session.query(OfficialSource)
                .filter(OfficialSource.url == source.url)
                .first()
            )
            canonical_opp: Optional[ScholarshipOpportunity] = (
                existing_source_record.opportunity if existing_source_record else None
            )

            if not success:
                run_record.sources_failed += 1
                err_msg = f"Fetch failed for {source.url}: {fetch_res.status_category.value} - {fetch_res.error_message}"
                errors.append(err_msg)
                logger.warning(err_msg)

                # If canonical opportunity exists, record source liveness failure without wiping data
                if canonical_opp:
                    liv_status = (
                        LivenessStatus.DEAD_LINK
                        if fetch_res.status_category == FetchStatusCategory.HTTP_404
                        else LivenessStatus.UNREACHABLE
                    )
                    log_rec = SourceLivenessLog(
                        scholarship_id=canonical_opp.id,
                        source_url=source.url,
                        liveness_status=liv_status.value,
                        http_status=fetch_res.http_status,
                        redirect_chain_json=json.dumps(fetch_res.redirect_chain),
                        error_message=fetch_res.error_message,
                        checked_at=now,
                    )
                    session.add(log_rec)
                continue

            run_record.sources_succeeded += 1

            # Check content SHA-256 change
            content_changed = (
                previous_content_hash != fetch_res.content_sha256
                if previous_content_hash
                else True
            )

            if not content_changed and not force_reverify and canonical_opp is not None:
                # Content hash unchanged; verified facts remain intact
                logger.info(f"Source content unchanged for {source.url}. Preserving verified canonical state.")
                run_record.opportunities_scanned += 1
                continue

            # Content changed or initial ingestion: Extract candidate opportunity
            staging_res = self.runner.ingest_html(
                html=fetch_res.content,  # type: ignore
                source_url=source.url,
                authority_tier=source_tier,
                fetch_result=fetch_res,
            )

            if not staging_res.candidate:
                warning_msg = f"Candidate extraction yielded no opportunity for {source.url}"
                errors.append(warning_msg)
                logger.warning(warning_msg)
                continue

            candidate = staging_res.candidate
            run_record.opportunities_scanned += 1

            # Check if canonical exists by fingerprint/slug if not matched by source URL
            if canonical_opp is None:
                slug = candidate.title.lower().replace(" ", "-").replace("'", "")
                canonical_opp = (
                    session.query(ScholarshipOpportunity)
                    .filter(ScholarshipOpportunity.slug == slug)
                    .first()
                )

            # Fact-level change detection
            fact_comp = ChangeDetector.compare_facts(
                canonical_opp=canonical_opp,
                candidate=candidate,
                old_hash=previous_content_hash,
                new_hash=fetch_res.content_sha256,
            )

            # Construct SourceLivenessResult for verification engine
            liveness_res = SourceLivenessResult(
                source_url=source.url,
                liveness_status=LivenessStatus.LIVE,
                http_status=fetch_res.http_status or 200,
                is_live=True,
                is_soft_404=False,
                final_url=fetch_res.redirect_chain[-1] if fetch_res.redirect_chain else source.url,
                redirect_chain=fetch_res.redirect_chain,
                content_sha256=fetch_res.content_sha256,
                content_type=fetch_res.headers.get("content-type"),
                checked_at=now,
            )

            # Run deterministic verification engine
            decision = self.verification_engine.evaluate(
                candidate=candidate,
                liveness_result=liveness_res,
                canonical_opportunity=canonical_opp,
                target_cycle=candidate.academic_cycle,
            )

            run_record.conflicts_detected += len(decision.conflicts)

            if decision.can_promote:
                is_new = (canonical_opp is None)
                promoted = CanonicalPromoter.promote_candidate(
                    session=session,
                    candidate=candidate,
                    decision=decision,
                    canonical_opp=canonical_opp,
                )
                if is_new:
                    run_record.opportunities_created += 1
                else:
                    run_record.opportunities_updated += 1
            else:
                logger.info(
                    f"Candidate '{candidate.title}' unpromotable with state '{decision.overall_state.value}': {decision.rationale}"
                )

        # Finalize run
        run_record.status = "COMPLETED"
        run_record.finished_at = datetime.now(timezone.utc)
        if errors:
            run_record.error_log_json = json.dumps(errors)

        session.commit()
        session.refresh(run_record)

        return PipelineRunSummary(
            run_id=run_record.id,
            run_type=run_record.run_type,
            status=run_record.status,
            sources_attempted=run_record.sources_attempted,
            sources_succeeded=run_record.sources_succeeded,
            sources_failed=run_record.sources_failed,
            opportunities_scanned=run_record.opportunities_scanned,
            opportunities_updated=run_record.opportunities_updated,
            opportunities_created=run_record.opportunities_created,
            conflicts_detected=run_record.conflicts_detected,
            errors=errors,
        )
