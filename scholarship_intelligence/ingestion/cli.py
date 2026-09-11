"""Command Line Interface for live scholarship ingestion and re-verification."""
import argparse
from datetime import datetime, timezone
import json
import sys
from typing import Optional

from scholarship_intelligence.db.session import get_db_session, init_db
from scholarship_intelligence.ingestion.freshness import FreshnessClassifier
from scholarship_intelligence.ingestion.pipeline import IngestionPipeline
from scholarship_intelligence.ingestion.source_registry import SourceRegistry
from scholarship_intelligence.models.ingestion_run import IngestionRun
from scholarship_intelligence.models.ingestion_source import IngestionSource
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.verification.engine import VerificationEngine


def parse_reference_time(ref_str: Optional[str]) -> Optional[datetime]:
    """Parses optional ISO or YYYY-MM-DD date string into UTC datetime."""
    if not ref_str:
        return None
    try:
        if "T" in ref_str:
            dt = datetime.fromisoformat(ref_str)
        else:
            dt = datetime.strptime(ref_str, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        print(f"Error: Invalid reference-time format '{ref_str}': {e}", file=sys.stderr)
        sys.exit(1)


def seed_sources_command(args: argparse.Namespace) -> None:
    """Seeds authentic sources into the database."""
    init_db()
    with get_db_session() as session:
        created = SourceRegistry.seed_default_sources(session)
        total = session.query(IngestionSource).count()
        print(f"Source Seeding Complete: {len(created)} new sources created ({total} total active sources in registry).")
        for s in session.query(IngestionSource).all():
            print(f" - [{s.authority_tier}] {s.name} ({s.url}) [Interval: {s.fetch_interval_hours}h]")


def run_command(args: argparse.Namespace) -> None:
    """Executes a live ingestion run."""
    init_db()
    ref_time = parse_reference_time(args.reference_time)
    with get_db_session() as session:
        sources = None
        if args.due_only:
            sources = SourceRegistry.get_active_sources(session, due_only=True, reference_time=ref_time)
            print(f"Executing due-only crawl for {len(sources)} sources.")

        pipeline = IngestionPipeline()
        summary = pipeline.run(
            session=session,
            sources=sources,
            run_type="MANUAL" if not args.due_only else "SCHEDULED",
            force_reverify=args.force_reverify,
            reference_time=ref_time,
        )

        print("\n=== Live Ingestion Run Summary ===")
        print(f"Run ID:                 {summary.run_id}")
        print(f"Status:                 {summary.status}")
        print(f"Sources Attempted:      {summary.sources_attempted}")
        print(f"Sources Succeeded:      {summary.sources_succeeded}")
        print(f"Sources Failed:         {summary.sources_failed}")
        print(f"Opportunities Scanned:  {summary.opportunities_scanned}")
        print(f"Opportunities Created:  {summary.opportunities_created}")
        print(f"Opportunities Updated:  {summary.opportunities_updated}")
        print(f"Conflicts Detected:     {summary.conflicts_detected}")
        if summary.errors:
            print(f"Warnings/Errors ({len(summary.errors)}):")
            for err in summary.errors:
                print(f"  * {err}")


def reverify_command(args: argparse.Namespace) -> None:
    """Executes deterministic re-verification on canonical opportunities."""
    init_db()
    ref_time = parse_reference_time(args.reference_time)
    with get_db_session() as session:
        query = session.query(ScholarshipOpportunity)
        if args.opportunity_id:
            query = query.filter(ScholarshipOpportunity.id == args.opportunity_id)

        opportunities = query.all()
        if not opportunities:
            print("No opportunities found matching criteria.", file=sys.stderr)
            return

        print(f"\n=== Re-verifying {len(opportunities)} Opportunity Records ===")
        for opp in opportunities:
            freshness = FreshnessClassifier.classify(opp, reference_time=ref_time)
            print(f"Opportunity: {opp.title} ({opp.id})")
            print(f"  Verification Status: {opp.verification_status}")
            print(f"  Freshness Level:     {freshness.level.value} (Stale={freshness.is_stale})")
            print(f"  Message:             {freshness.message}")


def status_command(args: argparse.Namespace) -> None:
    """Displays registry status and recent ingestion runs."""
    init_db()
    with get_db_session() as session:
        sources = session.query(IngestionSource).all()
        runs = session.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(10).all()
        opp_count = session.query(ScholarshipOpportunity).count()

        print("\n=== Registered Ingestion Sources ===")
        print(f"Total Sources: {len(sources)}")
        for s in sources:
            status_str = "ACTIVE" if s.is_active else "INACTIVE"
            last_crawl = s.last_crawled_at.strftime("%Y-%m-%d %H:%M UTC") if s.last_crawled_at else "NEVER"
            print(f"[{status_str}] {s.name}")
            print(f"  URL: {s.url}")
            print(f"  Tier: {s.authority_tier} | Last Crawl: {last_crawl} | Last HTTP: {s.last_http_status or 'N/A'}")

        print(f"\n=== Total Canonical Opportunities: {opp_count} ===")

        print("\n=== Recent Ingestion Runs ===")
        if not runs:
            print("No runs recorded yet.")
        for r in runs:
            started = r.started_at.strftime("%Y-%m-%d %H:%M UTC") if r.started_at else "UNKNOWN"
            print(f"Run {r.id[:8]}... [{r.run_type}] Status: {r.status} (Started: {started})")
            print(f"  Attempted: {r.sources_attempted} | Succeeded: {r.sources_succeeded} | Failed: {r.sources_failed} | Created: {r.opportunities_created} | Updated: {r.opportunities_updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scholarship Intelligence Live Ingestion & Re-verification CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Seed sources
    seed_p = subparsers.add_parser("seed-sources", help="Seed default authentic scholarship sources")
    seed_p.set_defaults(func=seed_sources_command)

    # Run ingestion
    run_p = subparsers.add_parser("run", help="Run live ingestion pipeline")
    run_p.add_argument("--force-reverify", action="store_true", help="Force candidate extraction even if content hash unchanged")
    run_p.add_argument("--due-only", action="store_true", help="Only crawl sources that are due based on fetch interval")
    run_p.add_argument("--reference-time", type=str, default=None, help="Explicit reference time for deterministic crawl evaluation (YYYY-MM-DD or ISO)")
    run_p.set_defaults(func=run_command)

    # Re-verify
    rev_p = subparsers.add_parser("reverify", help="Re-verify canonical opportunities")
    rev_p.add_argument("--opportunity-id", type=str, default=None, help="Target a specific opportunity ID")
    rev_p.add_argument("--reference-time", type=str, default=None, help="Explicit reference time for freshness evaluation")
    rev_p.set_defaults(func=reverify_command)

    # Status
    status_p = subparsers.add_parser("status", help="Show ingestion source and run status")
    status_p.set_defaults(func=status_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
