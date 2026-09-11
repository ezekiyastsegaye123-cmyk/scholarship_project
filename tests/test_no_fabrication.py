"""No-Fabrication Acceptance Test for Seed Data.

Enforceable Data-Integrity Rule:
1. A material fact has no provenance record -> FAILS.
2. A material fact is marked as known while its verification status is UNVERIFIED -> FAILS.
3. A material fact is missing evidence but represented as a concrete guessed value -> FAILS.
4. Competitiveness or acceptance percentages fabricated -> FAILS.
"""
import pytest
from scholarship_intelligence.domain.enums import TriState, VerificationState
from scholarship_intelligence.models import (
    OfficialSource,
    ScholarshipOpportunity,
    VerificationRecord,
)


def test_no_fabricated_facts_in_seeded_opportunities(seeded_db_session):
    """Audits all seeded opportunities in the database for strict provenance and no fabrication."""
    opportunities = seeded_db_session.query(ScholarshipOpportunity).all()
    assert len(opportunities) >= 15, f"Expected at least 15 verified seed opportunities, found {len(opportunities)}"
    assert len(opportunities) <= 25, f"Expected at most 25 seed opportunities, found {len(opportunities)}"

    for opp in opportunities:
        # 1. Geographic & Degree Scope Verification
        assert opp.destination_country == "US", f"{opp.slug}: Destination must be US"
        assert opp.target_degree_level == "BACHELOR", f"{opp.slug}: Degree level must be BACHELOR"

        # 2. Provenance Anchor Check
        assert len(opp.official_sources) >= 1, f"{opp.slug}: Missing official provenance source"
        primary_source = [s for s in opp.official_sources if s.is_primary]
        assert len(primary_source) >= 1, f"{opp.slug}: Missing designated primary official source"
        assert primary_source[0].url.startswith("https://"), f"{opp.slug}: Official URL must be HTTPS"
        assert len(primary_source[0].extracted_text_snippet or "") > 0, f"{opp.slug}: Missing extracted evidence text"

        # 3. Verification State & Citation Audit
        if opp.verification_status == VerificationState.VERIFIED.value:
            v_records = opp.verification_records
            assert len(v_records) >= 1, f"{opp.slug}: Marked as VERIFIED but lacks VerificationRecord"
            for vr in v_records:
                assert vr.verification_state == VerificationState.VERIFIED.value
                assert len(vr.evidence_quote) >= 10, f"{opp.slug}: Verification evidence quote too short or empty"
                assert vr.evidence_url.startswith("http"), f"{opp.slug}: Verification evidence URL must be valid"
        elif opp.verification_status == VerificationState.UNVERIFIED.value:
            # Unverified opportunities cannot claim concrete unverified facts
            assert opp.international_students_allowed == TriState.UNKNOWN.value, (
                f"{opp.slug}: UNVERIFIED listing cannot claim known international eligibility"
            )

        # 4. Deadlines Evidence Audit
        for deadline in opp.deadlines:
            if deadline.is_exact_date and deadline.deadline_date is not None:
                assert deadline.academic_cycle == "2026-2027", f"{opp.slug}: Inconsistent academic cycle"
                assert (deadline.source_evidence_snippet or deadline.context_description), (
                    f"{opp.slug}: Concrete deadline date lacks evidence snippet or description"
                )

        # 5. Funding Components Evidence Audit
        if opp.award:
            for comp in opp.award.funding_components:
                assert (comp.source_evidence_snippet or comp.description), (
                    f"{opp.slug}: Funding component lacks explanatory evidence snippet"
                )

        # 6. Negative Check: No Fabricated Numerical Competitiveness or Fake Trust Scores
        assert not hasattr(opp, "trust_score"), f"{opp.slug}: Forbidden trust_score found on opportunity model"
        assert not hasattr(opp, "overall_fit_score"), f"{opp.slug}: Forbidden overall_fit_score found"
        assert not hasattr(opp, "acceptance_probability"), f"{opp.slug}: Fabricated acceptance_probability found"
