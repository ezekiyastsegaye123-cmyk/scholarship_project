"""Tests for idempotent seed data population."""
from scholarship_intelligence.models import (
    Award,
    Deadline,
    FundingComponent,
    OfficialSource,
    Provider,
    ScholarshipOpportunity,
    University,
    VerificationRecord,
)
from scholarship_intelligence.seed.loader import seed_database


def test_seed_idempotency(db_session):
    """Verifies that running the seed loader multiple times creates records only once."""
    # First seed run
    stats1 = seed_database(db_session)
    assert stats1["opportunities_created"] == 18
    assert stats1["universities_created"] == 18
    assert stats1["providers_created"] == 1
    assert stats1["verification_records_created"] == 18

    count_opps_1 = db_session.query(ScholarshipOpportunity).count()
    count_univs_1 = db_session.query(University).count()
    count_awards_1 = db_session.query(Award).count()
    count_deadlines_1 = db_session.query(Deadline).count()

    assert count_opps_1 == 18
    assert count_univs_1 == 18

    # Second seed run on same session
    stats2 = seed_database(db_session)
    assert stats2["opportunities_created"] == 0
    assert stats2["universities_created"] == 0
    assert stats2["providers_created"] == 0
    assert stats2["awards_created"] == 0
    assert stats2["funding_components_created"] == 0
    assert stats2["deadlines_created"] == 0
    assert stats2["official_sources_created"] == 0
    assert stats2["verification_records_created"] == 0

    count_opps_2 = db_session.query(ScholarshipOpportunity).count()
    assert count_opps_2 == count_opps_1

    # Verify Clark Global Scholars details
    clark = db_session.query(ScholarshipOpportunity).filter_by(slug="clark-global-scholars-program").first()
    assert clark is not None
    assert clark.university.name == "Clark University"
    assert len(clark.official_sources) == 1
    assert clark.official_sources[0].source_domain == "clarku.edu"
    assert clark.award.funding_components[0].amount_min == 15000.0
    assert clark.award.funding_components[0].amount_max == 25000.0
    assert len(clark.deadlines) == 2
    assert len(clark.verification_records) == 1
    assert len(clark.conflict_records) == 1


def test_seed_transactional_rollback(db_session, monkeypatch):
    """Verifies that if an error occurs during seeding, the transaction rolls back cleanly."""
    import pytest
    from scholarship_intelligence.seed import loader

    # Force an exception during seeding
    def faulty_compute(*args, **kwargs):
        raise RuntimeError("Simulated transient pipeline failure")

    monkeypatch.setattr(loader, "compute_fingerprint", faulty_compute)

    with pytest.raises(RuntimeError, match="Simulated transient pipeline failure"):
        loader.seed_database(db_session)

    # Verify no partial records were committed
    assert db_session.query(ScholarshipOpportunity).count() == 0
    assert db_session.query(Award).count() == 0
