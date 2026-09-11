"""SQLAlchemy model for IngestionRun audit trail."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text

from scholarship_intelligence.models.base import Base, TimestampMixin, generate_uuid


class IngestionRun(Base, TimestampMixin):
    __tablename__ = "ingestion_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_type = Column(String(50), nullable=False, default="SCHEDULED")  # SCHEDULED, MANUAL, REVERIFY
    status = Column(String(50), nullable=False, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime, nullable=True)
    sources_attempted = Column(Integer, nullable=False, default=0)
    sources_succeeded = Column(Integer, nullable=False, default=0)
    sources_failed = Column(Integer, nullable=False, default=0)
    opportunities_scanned = Column(Integer, nullable=False, default=0)
    opportunities_updated = Column(Integer, nullable=False, default=0)
    opportunities_created = Column(Integer, nullable=False, default=0)
    conflicts_detected = Column(Integer, nullable=False, default=0)
    error_log_json = Column(Text, nullable=True)
    reference_time = Column(DateTime, nullable=True)
