"""CRITICAL REGRESSION TEST: Golden Hierarchy Enforcement.

Verifies that Phase 1B ingestion NEVER directly overwrites verified database records.
The hierarchy is strictly:
Official source -> extracted evidence -> normalized fact -> verification state -> conflict if disagreement
NOT:
scraped value -> overwrite database.
"""
from datetime import date
from sqlalchemy.orm import Session
import pytest

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.ingestion.runner import IngestionRunner
from scholarship_intelligence.models.funding import Award
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.university import University
from scholarship_intelligence.models.verification import VerificationRecord
from scholarship_intelligence.models.source import OfficialSource


def test_golden_hierarchy_no_overwrite_of_verified_record(db_session: Session):
    """MANDATORY REGRESSION TEST (Section 22):
    
    1. Sets up an existing canonical record with verification_state = VERIFIED.
    2. Runs Phase 1B ingestion over a webpage reporting conflicting information.
    3. Asserts that the canonical verified record in the database remains completely UNCHANGED.
    4. Asserts that new information is preserved strictly in candidate staging.
    """
    # 1. Establish existing VERIFIED scholarship in canonical database
    univ = University(
        name="Amherst College",
        city="Amherst",
        state="MA",
        country="US",
        admissions_need_policy="NEED_BLIND_INTERNATIONAL",
    )
    db_session.add(univ)
    db_session.flush()

    verified_opp = ScholarshipOpportunity(
        university_id=univ.id,
        title="Amherst Need-Based Financial Aid for International Students",
        slug="amherst-need-based-aid",
        target_degree_level="BACHELOR",
        destination_country="US",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES.value,
        requires_sat=TriState.NO.value,
        requires_act=TriState.NO.value,
        requires_css_profile=TriState.YES.value,
        financial_need_required=TriState.YES.value,
        verification_status=VerificationState.VERIFIED.value,
        fingerprint_sha256="canonical_amherst_verified_fingerprint",
    )
    db_session.add(verified_opp)
    db_session.flush()

    award = Award(
        scholarship_id=verified_opp.id,
        funding_classification=FundingClassification.FULL_FUNDING.value,
        title="Amherst Need-Based Aid Package",
        is_renewable=TriState.YES.value,
        estimated_annual_value_usd=70000.0,
    )
    db_session.add(award)

    ver_rec = VerificationRecord(
        scholarship_id=verified_opp.id,
        verification_state=VerificationState.VERIFIED.value,
        verifier_identity="senior_data_architect",
        verification_method="OFFICIAL_MANUAL_AUDIT",
        evidence_url="https://www.amherst.edu/admission/financialaid/international",
        evidence_quote="Amherst meets 100% of calculated need for all admitted students.",
    )
    db_session.add(ver_rec)
    db_session.commit()

    # Capture initial database state
    original_opp_id = verified_opp.id
    original_title = verified_opp.title
    original_verification_state = verified_opp.verification_status
    original_sat_state = verified_opp.requires_sat
    original_award_val = award.estimated_annual_value_usd

    # 2. Simulate ingesting an external page claiming conflicting/different values
    # e.g., claiming SAT is required and award is fixed at $20,000
    conflicting_html = """
    <html>
    <head><title>Amherst Aid Update Notice</title></head>
    <body>
        <h1>Amherst Need-Based Financial Aid for International Students</h1>
        <p>New policy: All applicants must submit SAT scores. SAT is required.</p>
        <p>Annual award is limited to $20,000 per year.</p>
        <p>Deadline is December 15, 2025.</p>
    </body>
    </html>
    """

    runner = IngestionRunner()
    staging_result = runner.ingest_html(
        html=conflicting_html,
        source_url="https://thirdparty-aggregator.com/amherst-aid",
        authority_tier=AuthorityTier.THIRD_PARTY,
    )

    # 3. Assert candidate staging received the candidate facts
    assert staging_result.candidate is not None
    assert staging_result.candidate.requires_sat == TriState.YES
    assert staging_result.candidate.award is not None
    assert staging_result.candidate.award.components[0].amount_min == 20000.0

    # 4. CRITICAL ASSERTION: The canonical database was NOT modified or overwritten!
    db_session.expire_all()  # Refresh from disk/DB
    refreshed_opp = db_session.query(ScholarshipOpportunity).filter_by(id=original_opp_id).one()
    refreshed_award = db_session.query(Award).filter_by(scholarship_id=original_opp_id).one()

    # The canonical record MUST remain untouched
    assert refreshed_opp.verification_status == original_verification_state == VerificationState.VERIFIED.value
    assert refreshed_opp.requires_sat == original_sat_state == TriState.NO.value
    assert refreshed_award.estimated_annual_value_usd == original_award_val == 70000.0
    assert refreshed_opp.title == original_title

    # Total opportunities count in canonical DB must remain exactly 1
    assert db_session.query(ScholarshipOpportunity).count() == 1
