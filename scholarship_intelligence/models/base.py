"""SQLAlchemy declarative base and common model mixins."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Provides created_at and updated_at timestamps in UTC."""
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


def generate_uuid() -> str:
    """Generates standard RFC 4122 UUID4 string for database portability."""
    return str(uuid.uuid4())
