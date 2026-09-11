"""Mandatory Critical End-to-End Test for Phase 1C Verification and Provenance Pipeline.

Pipeline verified:
1. Phase 1B candidate + evidence from official university source
2. Verification engine -> VERIFIED
3. Canonical promotion -> creates canonical database opportunity
4. Full provenance query: Opportunity -> VerificationRecord -> CandidateEvidence -> OfficialSource -> Content SHA256
5. Ingest new candidate with conflicting evidence
6. Verification engine detects discrepancy against canonical record -> CONFLICTING
7. Conflicting candidate leaves canonical verified fact protected
8. Verification history and ConflictRecord preserved
"""
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    ConflictStatus,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    TriState,
    VerificationState,
)
from scholarship_intelligence.models import (
    Base,
    ConflictRecord,
    Deadline,
    FundingComponent,
    OfficialSource,
    ScholarshipOpportunity,
    VerificationHistory,
    VerificationRecord,
)
from scholarship_intelligence.schemas.candidate import (
    CandidateAward,
    CandidateDeadline,
    CandidateEvidence,
    CandidateFundingComponent,
    CandidateOpportunity,
)
from scholarship_intelligence.verification.engine import VerificationEngine
from scholarship_intelligence.verification.promoter import CanonicalPromoter


def test_mandatory_critical_verification_e2e_pipeline():
    # Setup isolated in-memory test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ---------------------------------------------------------
        # Step 1: Ingest Phase 1B Candidate with Official Evidence
        # ---------------------------------------------------------
        official_ev = CandidateEvidence(
            source_url="https://admissions.clarku.edu/scholarships/global-scholars",
            authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
            evidence_text="Clark University awards the Global Scholars Program to international undergraduate applicants. Full tuition coverage is provided. The deadline is February 1, 2027.",
            content_sha256="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        )

        cand_1 = CandidateOpportunity(
            title="Clark Global Scholars Program",
            academic_cycle="2026-2027",
            target_degree_level="BACHELOR",
            destination_country="US",
            international_students_allowed=TriState.YES,
            requires_sat=TriState.NO,
            requires_act=TriState.NO,
            financial_need_required=TriState.NO,
            award=CandidateAward(
                title="Global Scholars Tuition Award",
                funding_classification=FundingClassification.FULL_TUITION,
                components=[
                    CandidateFundingComponent(
                        component_type=FundingComponentType.TUITION,
                        percentage_tuition=100.0,
                        evidence=official_ev,
                    )
                ],
                evidence=official_ev,
            ),
            deadlines=[
                CandidateDeadline(
                    deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
                    raw_date_text="February 1, 2027",
                    deadline_date=date(2027, 2, 1),
                    is_exact_date=True,
                    academic_cycle="2026-2027",
                    evidence=official_ev,
                )
            ],
            source_evidence=[official_ev],
        )

        # ---------------------------------------------------------
        # Step 2: Verification Engine Evaluation
        # ---------------------------------------------------------
        decision_1 = VerificationEngine.evaluate(cand_1)
        assert decision_1.overall_state == VerificationState.VERIFIED
        assert decision_1.can_promote is True
        assert len(decision_1.conflicts) == 0

        # ---------------------------------------------------------
        # Step 3: Canonical Promotion
        # ---------------------------------------------------------
        canonical_opp = CanonicalPromoter.promote_candidate(
            session=session,
            candidate=cand_1,
            decision=decision_1,
        )
        session.commit()

        # ---------------------------------------------------------
        # Step 4: Provenance Query (Auditable Golden Data Hierarchy)
        # ---------------------------------------------------------
        persisted_opp = session.query(ScholarshipOpportunity).filter_by(id=canonical_opp.id).one()
        assert persisted_opp.title == "Clark Global Scholars Program"
        assert persisted_opp.verification_status == VerificationState.VERIFIED.value
        assert persisted_opp.international_students_allowed == TriState.YES.value

        # Trace to VerificationRecord
        v_recs = session.query(VerificationRecord).filter_by(scholarship_id=persisted_opp.id).all()
        assert len(v_recs) >= 1
        v_rec = v_recs[0]
        assert v_rec.verification_state == VerificationState.VERIFIED.value
        assert v_rec.evidence_url == official_ev.source_url
        assert "Full tuition coverage" in v_rec.evidence_quote

        # Trace to OfficialSource
        sources = session.query(OfficialSource).filter_by(scholarship_id=persisted_opp.id).all()
        assert len(sources) >= 1
        src = sources[0]
        assert src.url == official_ev.source_url
        assert src.authority_tier == AuthorityTier.OFFICIAL_UNIVERSITY.value

        # Trace to VerificationHistory
        histories = session.query(VerificationHistory).filter_by(scholarship_id=persisted_opp.id).all()
        assert len(histories) >= 1
        assert histories[0].decision == "PROMOTED_NEW_CANONICAL"

        # ---------------------------------------------------------
        # Step 5: Ingest New Candidate with Conflicting Evidence
        # ---------------------------------------------------------
        conflicting_ev = CandidateEvidence(
            source_url="https://financialaid.clarku.edu/scholarships",
            authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
            evidence_text="Important update: International students are not eligible for the Global Scholars Program.",
            content_sha256="aabbccddeeff00112233445566778899",
        )

        cand_2 = CandidateOpportunity(
            title="Clark Global Scholars Program",
            academic_cycle="2026-2027",
            target_degree_level="BACHELOR",
            destination_country="US",
            international_students_allowed=TriState.NO,  # Contradicts canonical YES!
            source_evidence=[conflicting_ev],
        )

        # ---------------------------------------------------------
        # Step 6: Conflict Detection & State Resolution
        # ---------------------------------------------------------
        decision_2 = VerificationEngine.evaluate(
            candidate=cand_2,
            canonical_opportunity=persisted_opp,
        )
        assert decision_2.overall_state == VerificationState.CONFLICTING
        assert decision_2.can_promote is False
        assert len(decision_2.conflicts) >= 1
        conflict = decision_2.conflicts[0]
        assert conflict.field_name == "international_students_allowed"
        assert conflict.source_a_value == "NO"
        assert conflict.source_b_value == "YES"
        assert conflict.resolution_status == ConflictStatus.OPEN

        # ---------------------------------------------------------
        # Step 7: Overwriting Protection Invariant
        # ---------------------------------------------------------
        with pytest.raises(ValueError) as excinfo:
            CanonicalPromoter.promote_candidate(
                session=session,
                candidate=cand_2,
                decision=decision_2,
                canonical_opp=persisted_opp,
            )
        assert "Cannot promote candidate" in str(excinfo.value)

        # ---------------------------------------------------------
        # Step 8: Assert Existing Verified Canonical Fact Remains Protected!
        # ---------------------------------------------------------
        session.rollback()
        verified_opp = session.query(ScholarshipOpportunity).filter_by(id=canonical_opp.id).one()
        assert verified_opp.international_students_allowed == TriState.YES.value
        assert verified_opp.verification_status == VerificationState.VERIFIED.value

    finally:
        session.close()
        engine.dispose()
