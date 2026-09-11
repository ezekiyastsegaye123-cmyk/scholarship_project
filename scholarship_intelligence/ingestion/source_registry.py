"""Source Registry for managing active/inactive scholarship ingestion targets."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import urllib.parse
from sqlalchemy.orm import Session

from scholarship_intelligence.domain.enums import AuthorityTier
from scholarship_intelligence.models.ingestion_source import IngestionSource

DEFAULT_SOURCES = [
    {
        "name": "Harvard Financial Aid - International Students",
        "url": "https://college.harvard.edu/financial-aid/how-aid-works/international-students",
        "authority_tier": AuthorityTier.OFFICIAL_UNIVERSITY.value,
        "fetch_interval_hours": 24,
        "description": "Official Harvard University undergraduate financial aid policies and eligibility for international students.",
    },
    {
        "name": "Stanford Knight-Hennessy Scholars Program",
        "url": "https://knight-hennessy.stanford.edu/admission/planning-apply/eligibility",
        "authority_tier": AuthorityTier.OFFICIAL_UNIVERSITY.value,
        "fetch_interval_hours": 24,
        "description": "Official Stanford Knight-Hennessy Scholars eligibility criteria and deadline information.",
    },
    {
        "name": "Rhodes Trust - Global Scholarship",
        "url": "https://www.rhodeshouse.ox.ac.uk/scholarships/the-rhodes-scholarship/",
        "authority_tier": AuthorityTier.OFFICIAL_PROVIDER.value,
        "fetch_interval_hours": 24,
        "description": "Official Rhodes Trust postgraduate scholarship eligibility, criteria, and governance guidelines.",
    },
    {
        "name": "Gates Cambridge Scholarship - Criteria & Deadlines",
        "url": "https://www.gatescambridge.org/programme/the-scholarship/",
        "authority_tier": AuthorityTier.OFFICIAL_PROVIDER.value,
        "fetch_interval_hours": 24,
        "description": "Official Gates Cambridge postgraduate scholarship criteria, stipend details, and deadlines.",
    },
    {
        "name": "DAAD - German Academic Exchange Service Scholarships",
        "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
        "authority_tier": AuthorityTier.GOVERNMENT.value,
        "fetch_interval_hours": 48,
        "description": "Official German federal academic exchange service funding opportunities for international students.",
    },
    {
        "name": "Fulbright Foreign Student Program",
        "url": "https://foreign.fulbrightonline.org/about/foreign-student-program",
        "authority_tier": AuthorityTier.GOVERNMENT.value,
        "fetch_interval_hours": 48,
        "description": "Official US Department of State international exchange program guidelines and requirements.",
    },
]


class SourceRegistry:
    """Manages ingestion sources in the database."""

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts normalized domain name from URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname.lower() if parsed.hostname else "unknown"

    @classmethod
    def seed_default_sources(cls, db: Session) -> List[IngestionSource]:
        """Seeds default authentic scholarship sources idempotently."""
        created = []
        for src_data in DEFAULT_SOURCES:
            existing = db.query(IngestionSource).filter(IngestionSource.url == src_data["url"]).first()
            if not existing:
                domain = cls.extract_domain(src_data["url"])
                source = IngestionSource(
                    name=src_data["name"],
                    url=src_data["url"],
                    source_domain=domain,
                    authority_tier=src_data["authority_tier"],
                    fetch_interval_hours=src_data.get("fetch_interval_hours", 24),
                    is_active=True,
                    description=src_data.get("description"),
                )
                db.add(source)
                created.append(source)
        if created:
            db.commit()
            for s in created:
                db.refresh(s)
        return created

    @classmethod
    def register_source(
        cls,
        db: Session,
        name: str,
        url: str,
        authority_tier: AuthorityTier = AuthorityTier.OFFICIAL_UNIVERSITY,
        fetch_interval_hours: int = 24,
        description: Optional[str] = None,
    ) -> IngestionSource:
        """Registers a new ingestion source or returns existing one."""
        existing = db.query(IngestionSource).filter(IngestionSource.url == url).first()
        if existing:
            return existing

        domain = cls.extract_domain(url)
        tier_val = authority_tier.value if isinstance(authority_tier, AuthorityTier) else str(authority_tier)
        source = IngestionSource(
            name=name,
            url=url,
            source_domain=domain,
            authority_tier=tier_val,
            fetch_interval_hours=fetch_interval_hours,
            is_active=True,
            description=description,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def get_active_sources(
        cls,
        db: Session,
        due_only: bool = False,
        reference_time: Optional[datetime] = None,
    ) -> List[IngestionSource]:
        """Retrieves active sources, optionally filtered by due crawl schedule."""
        ref_time = reference_time or datetime.now(timezone.utc)
        query = db.query(IngestionSource).filter(IngestionSource.is_active == True)
        sources = query.all()

        if not due_only:
            return sources

        due_sources = []
        for s in sources:
            if s.last_crawled_at is None:
                due_sources.append(s)
            else:
                last_crawl = s.last_crawled_at
                if last_crawl.tzinfo is None:
                    last_crawl = last_crawl.replace(tzinfo=timezone.utc)
                if ref_time.tzinfo is None:
                    ref_time = ref_time.replace(tzinfo=timezone.utc)
                
                next_due = last_crawl + timedelta(hours=s.fetch_interval_hours)
                if ref_time >= next_due:
                    due_sources.append(s)
        return due_sources

    @classmethod
    def record_crawl_result(
        cls,
        db: Session,
        source_id: str,
        http_status: int,
        content_sha256: Optional[str],
        crawled_at: datetime,
        success: bool,
    ) -> Optional[IngestionSource]:
        """Updates source status and hash metrics after a crawl attempt."""
        source = db.query(IngestionSource).filter(IngestionSource.id == source_id).first()
        if not source:
            return None

        source.last_crawled_at = crawled_at
        source.last_http_status = http_status
        if success:
            source.failure_count = 0
            if content_sha256:
                source.last_content_sha256 = content_sha256
        else:
            source.failure_count += 1

        db.commit()
        db.refresh(source)
        return source
