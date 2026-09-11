"""Tests for controlled canonical promotion, overwriting protections, and verification history audit."""
from datetime import date, datetime, timezone
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
from scholarship_intelligence.schemas.verification import ConflictRecordCreate, VerificationDecisionResult
from scholarship_intelligence.verification.promoter import CanonicalPromoter


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def valid_candidate():
    ev = CandidateEvidence(
        source_url="https://admissions.clarku.edu/scholarships",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="Full tuition scholarship awarded to international undergraduates.",
        content_sha256="hash123",
    )
    return CandidateOpportunity(
        title="Clark Presidential Scholarship",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.YES,
        requires_sat=TriState.NO,
        requires_act=TriState.NO,
        financial_need_required=TriState.NO,
        award=CandidateAward(
            title="Presidential Award",
            funding_classification=FundingClassification.FULL_TUITION,
            components=[
                CandidateFundingComponent(
                    component_type=FundingComponentType.TUITION,
                    percentage_tuition=100.0,
                    evidence=ev,
                )
            ],
            evidence=ev,
        ),
        deadlines=[
            CandidateDeadline(
                deadline_type=DeadlineType.SCHOLARSHIP_APPLICATION,
                raw_date_text="February 1, 2027",
                deadline_date=date(2027, 2, 1),
                is_exact_date=True,
                evidence=ev,
            )
        ],
        source_evidence=[ev],
    )


def test_verified_candidate_promotes_cleanly(db_session, valid_candidate):
    decision = VerificationDecisionResult(
        overall_state=VerificationState.VERIFIED,
        opportunity_title=valid_candidate.title,
        academic_cycle="2026-2027",
        rationale="All criteria verified from official university source.",
        can_promote=True,
    )

    opp = CanonicalPromoter.promote_candidate(db_session, valid_candidate, decision)
    assert opp.id is not None
    assert opp.verification_status == VerificationState.VERIFIED.value

    # Check that VerificationRecord was created
    v_recs = db_session.query(VerificationRecord).filter_by(scholarship_id=opp.id).all()
    assert len(v_recs) == 1
    assert v_recs[0].verification_state == VerificationState.VERIFIED.value

    # Check that initial history was created
    histories = db_session.query(VerificationHistory).filter_by(scholarship_id=opp.id).all()
    assert len(histories) == 1
    assert histories[0].decision == "PROMOTED_NEW_CANONICAL"


def test_unverified_candidate_cannot_promote(db_session, valid_candidate):
    decision = VerificationDecisionResult(
        overall_state=VerificationState.UNVERIFIED,
        opportunity_title=valid_candidate.title,
        academic_cycle="2026-2027",
        rationale="Source is unverified aggregator.",
        can_promote=False,
    )

    with pytest.raises(ValueError) as excinfo:
        CanonicalPromoter.promote_candidate(db_session, valid_candidate, decision)
    assert "Cannot promote candidate" in str(excinfo.value)


def test_canonical_fact_protected_from_conflicting_overwrite_with_history(db_session, valid_candidate):
    # Step 1: Promote initial verified opportunity
    dec1 = VerificationDecisionResult(
        overall_state=VerificationState.VERIFIED,
        opportunity_title=valid_candidate.title,
        academic_cycle="2026-2027",
        rationale="Initial official verification.",
        can_promote=True,
    )
    opp = CanonicalPromoter.promote_candidate(db_session, valid_candidate, dec1)
    db_session.commit()
    assert opp.international_students_allowed == TriState.YES.value

    # Step 2: New candidate claims international_students_allowed=NO with unresolved conflict
    conflicting_ev = CandidateEvidence(
        source_url="https://other-portal.edu/aid",
        authority_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        evidence_text="International students are not eligible for this award.",
        content_sha256="conflicthash",
    )
    cand2 = CandidateOpportunity(
        title="Clark Presidential Scholarship",
        academic_cycle="2026-2027",
        international_students_allowed=TriState.NO,
        source_evidence=[conflicting_ev],
    )

    open_conflict = ConflictRecordCreate(
        field_name="international_students_allowed",
        source_a_value="NO",
        source_a_url=conflicting_ev.source_url,
        source_a_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_a_evidence=conflicting_ev.evidence_text,
        source_b_value="YES",
        source_b_url="https://admissions.clarku.edu/scholarships",
        source_b_tier=AuthorityTier.OFFICIAL_UNIVERSITY,
        source_b_evidence="Full tuition scholarship awarded to international undergraduates.",
        resolution_status=ConflictStatus.OPEN,
        resolution_notes="Two official university pages disagree. Open conflict.",
    )

    dec2 = VerificationDecisionResult(
        overall_state=VerificationState.CONFLICTING,
        opportunity_title=cand2.title,
        academic_cycle="2026-2027",
        conflicts=[open_conflict],
        rationale="Unresolved conflict detected.",
        can_promote=False,  # Unresolved conflict cannot promote!
    )

    # Attempting to promote an unverified/conflicting decision raises ValueError
    with pytest.raises(ValueError):
        CanonicalPromoter.promote_candidate(db_session, cand2, dec2, canonical_opp=opp)

    # Verify that existing canonical value remains strictly untouched!
    refreshed_opp = db_session.query(ScholarshipOpportunity).filter_by(id=opp.id).one()
    assert refreshed_opp.international_students_allowed == TriState.YES.value
