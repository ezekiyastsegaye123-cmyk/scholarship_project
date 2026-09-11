"""Pytest fixtures for Phase 1A testing suite."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from scholarship_intelligence.models import Base
from scholarship_intelligence.seed.loader import seed_database


@pytest.fixture(scope="function")
def in_memory_engine():
    """Provides a thread-safe, isolated in-memory SQLite engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(in_memory_engine) -> Session:
    """Yields a transactional SQLAlchemy session on the fresh in-memory database."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)
    session = session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def seeded_db_session(db_session) -> Session:
    """Yields a session pre-populated with the authentic 18 seed opportunities."""
    seed_database(db_session)
    return db_session
