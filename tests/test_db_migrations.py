"""Tests for database migrations and schema creation."""
import os
import tempfile
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_clean_alembic_migration():
    """Verifies that Alembic successfully creates all tables from scratch on a clean DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        tmp_db_path = tmp_file.name

    try:
        db_url = f"sqlite:///{tmp_db_path}"
        os.environ["DATABASE_URL"] = db_url

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # Run migration to head
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        expected_tables = {
            "alembic_version",
            "providers",
            "universities",
            "scholarship_opportunities",
            "official_sources",
            "discovery_sources",
            "eligibility_rules",
            "requirements",
            "application_requirements",
            "awards",
            "funding_components",
            "deadlines",
            "verification_records",
            "conflict_records",
            "student_profiles",
            "ingestion_sources",
            "ingestion_runs",
        }
        assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"
        engine.dispose()
    finally:
        if os.path.exists(tmp_db_path):
            os.remove(tmp_db_path)
        os.environ.pop("DATABASE_URL", None)
