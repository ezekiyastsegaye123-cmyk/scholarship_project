"""Database session and engine management."""
import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from scholarship_intelligence.models.base import Base

DEFAULT_DATABASE_URL = "sqlite:///scholarship_intelligence.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Configure SQLite specific options (enable foreign keys)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None):
    """Initializes tables using metadata for direct/testing scenarios."""
    bind_engine = target_engine or engine
    Base.metadata.create_all(bind=bind_engine)


@contextmanager
def get_db_session(target_engine=None) -> Generator[Session, None, None]:
    """Context manager for reliable transactional DB session handling."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=target_engine or engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
