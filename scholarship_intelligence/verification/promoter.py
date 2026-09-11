from datetime import datetime, timezone
import json
from typing import Any, Optional
from sqlalchemy.orm import Session


from scholarship_intelligence.domain.enums import ConflictStatus, VerificationState
from scholarship_intelligence.models.conflict import ConflictRecord
from scholarship_intelligence.models.deadline import Deadline
from scholarship_intelligence.models.funding import Award, FundingComponent
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.source import OfficialSource
from scholarship_intelligence.models.source_liveness import SourceLivenessLog
from scholarship_intelligence.models.verification import VerificationRecord
from scholarship_intelligence.models.verification_history import VerificationHistory
from scholarship_intelligence.schemas.candidate import CandidateOpportunity
from scholarship_intelligence.schemas.verification import VerificationDecisionResult


class CanonicalPromoter:
    """Promotes verified candidate facts into canonical database records.
    
    CRITICAL INVARIANTS:
    1. A candidate fact NEVER overwrites a verified canonical fact without verification justification.
    2. Any unresolved conflict prevents overwriting and leaves existing verified data intact.
    3. Every replacement of a canonical fact preserves previous state in VerificationHistory.
    """

    @classmethod
    def promote_candidate(
        cls,
        session: Session,
        candidate: CandidateOpportunity,
        decision: VerificationDecisionResult,
        canonical_opp: Optional[ScholarshipOpportunity] = None,
    ) -> ScholarshipOpportunity:
        if not decision.can_promote:
            raise ValueError(
                f"Cannot promote candidate '{candidate.title}' with verification state '{decision.overall_state.value}'. "
                "Only VERIFIED or PARTIALLY_VERIFIED candidates satisfy canonical promotion criteria."
            )

        now = datetime.now(timezone.utc)
        primary_ev = candidate.source_evidence[0] if candidate.source_evidence else None

        # Determine if updating an existing opportunity or creating a new canonical record
        opp = canonical_opp
        if opp is None:
            import hashlib
            slug = candidate.title.lower().replace(" ", "-").replace("'", "")
            fp = hashlib.sha256(f"{slug}::{candidate.academic_cycle}".encode("utf-8")).hexdigest()

            opp = ScholarshipOpportunity(
                title=candidate.title,
                slug=slug,
                description=candidate.description,
                academic_cycle=candidate.academic_cycle,
                target_degree_level=candidate.target_degree_level,
                destination_country=candidate.destination_country,
                international_students_allowed=candidate.international_students_allowed.value,
                requires_sat=candidate.requires_sat.value,
                requires_act=candidate.requires_act.value,
                requires_css_profile=candidate.requires_css_profile.value,
                financial_need_required=candidate.financial_need_required.value,
                verification_status=decision.overall_state.value,
                fingerprint_sha256=fp,
            )
            session.add(opp)
            session.flush()

            # Record initial history
            session.add(
                VerificationHistory(
                    scholarship_id=opp.id,
                    field_name="initial_creation",
                    old_value=None,
                    new_value=opp.title,
                    old_evidence_url=None,
                    old_evidence_quote=None,
                    new_evidence_url=primary_ev.source_url if primary_ev else None,
                    new_evidence_quote=primary_ev.evidence_text if primary_ev else None,
                    decision="PROMOTED_NEW_CANONICAL",
                    reason=decision.rationale,
                    changed_at=now,
                )
            )
        else:
            # Updating existing canonical opportunity: check each field and protect verified facts
            cls._update_scalar_field_safely(
                session=session,
                opp=opp,
                field_name="international_students_allowed",
                candidate_val=candidate.international_students_allowed.value,
                candidate_ev=primary_ev,
                decision=decision,
                now=now,
            )
            cls._update_scalar_field_safely(
                session=session,
                opp=opp,
                field_name="requires_sat",
                candidate_val=candidate.requires_sat.value,
                candidate_ev=primary_ev,
                decision=decision,
                now=now,
            )
            cls._update_scalar_field_safely(
                session=session,
                opp=opp,
                field_name="financial_need_required",
                candidate_val=candidate.financial_need_required.value,
                candidate_ev=primary_ev,
                decision=decision,
                now=now,
            )

            # Update overall status only if not downgraded by an unresolved conflict
            has_conflict = any(c.resolution_status == ConflictStatus.OPEN for c in decision.conflicts)
            if not has_conflict:
                opp.verification_status = decision.overall_state.value

        # Persist OfficialSource
        if primary_ev:
            from urllib.parse import urlparse
            domain = urlparse(primary_ev.source_url).netloc or "unknown"
            source_rec = OfficialSource(
                scholarship_id=opp.id,
                url=primary_ev.source_url,
                source_domain=domain,
                authority_tier=primary_ev.authority_tier.value,
                is_primary=True,
                extracted_text_snippet=primary_ev.evidence_text,
                last_crawled_at=primary_ev.retrieved_at,
                last_http_status=primary_ev.http_status,
            )
            session.add(source_rec)

        # Persist VerificationRecord
        v_rec = VerificationRecord(
            scholarship_id=opp.id,
            verification_state=decision.overall_state.value,
            verifier_identity="Automated Verification Engine",
            verification_method="EVIDENCE_PROVENANCE_AUDIT",
            evidence_url=primary_ev.source_url if primary_ev else "https://example.org",
            evidence_quote=primary_ev.evidence_text if primary_ev else "Verified from structured evidence.",
            notes=decision.rationale,
            verified_at=now,
        )
        session.add(v_rec)

        # Persist any ConflictRecords
        for c in decision.conflicts:
            c_rec = ConflictRecord(
                scholarship_id=opp.id,
                field_name=c.field_name,
                source_a_value=c.source_a_value,
                source_a_url=c.source_a_url,
                source_b_value=c.source_b_value,
                source_b_url=c.source_b_url,
                source_a_tier=c.source_a_tier.value if c.source_a_tier else None,
                source_b_tier=c.source_b_tier.value if c.source_b_tier else None,
                source_a_evidence=c.source_a_evidence,
                source_b_evidence=c.source_b_evidence,
                resolution_status=c.resolution_status.value,
                resolution_notes=c.resolution_notes,
                resolved_at=c.resolved_at,
                recorded_at=c.recorded_at or now,
            )
            session.add(c_rec)

        # Persist SourceLivenessLog if checked
        if decision.liveness_result:
            liv = decision.liveness_result
            l_rec = SourceLivenessLog(
                scholarship_id=opp.id,
                source_url=liv.source_url,
                liveness_status=liv.liveness_status.value,
                http_status=liv.http_status,
                final_url=liv.final_url,
                redirect_chain_json=json.dumps(liv.redirect_chain),
                content_sha256=liv.content_sha256,
                content_type=liv.content_type,
                error_message=liv.error_message,
                checked_at=liv.checked_at,
            )
            session.add(l_rec)

        # Persist Award & FundingComponents if new
        if candidate.award and opp.award is None:
            award = Award(
                scholarship_id=opp.id,
                title=candidate.award.title,
                funding_classification=candidate.award.funding_classification.value,
                is_renewable=candidate.award.is_renewable.value,
                renewal_criteria=candidate.award.renewal_criteria,
                estimated_annual_value_usd=candidate.award.estimated_annual_value_usd,
            )
            session.add(award)
            session.flush()

            for comp in candidate.award.components:
                fc = FundingComponent(
                    award_id=award.id,
                    component_type=comp.component_type.value,
                    amount_min=comp.amount_min,
                    amount_max=comp.amount_max,
                    currency=comp.currency,
                    amount_period=comp.amount_period.value,
                    percentage_tuition=comp.percentage_tuition,
                    description=comp.description,
                    source_evidence_snippet=comp.evidence.evidence_text,
                )
                session.add(fc)

        # Persist Deadlines if new
        if candidate.deadlines and len(opp.deadlines) == 0:
            for dl in candidate.deadlines:
                d_rec = Deadline(
                    scholarship_id=opp.id,
                    deadline_type=dl.deadline_type.value,
                    deadline_date=dl.deadline_date,
                    is_exact_date=dl.is_exact_date,
                    academic_cycle=dl.academic_cycle or candidate.academic_cycle,
                    timezone=dl.timezone or "America/New_York",
                    varies_by_program=dl.varies_by_program,
                    context_description=dl.context_description,
                    source_evidence_snippet=dl.evidence.evidence_text,
                )
                session.add(d_rec)

        session.flush()
        return opp

    @classmethod
    def _update_scalar_field_safely(
        cls,
        session: Session,
        opp: ScholarshipOpportunity,
        field_name: str,
        candidate_val: str,
        candidate_ev: Optional[Any],
        decision: VerificationDecisionResult,
        now: datetime,
    ):
        curr_val = getattr(opp, field_name)
        if curr_val == candidate_val:
            return

        # Check if there is an open conflict on this field
        is_conflicting = any(c.field_name == field_name and c.resolution_status == ConflictStatus.OPEN for c in decision.conflicts)
        if is_conflicting:
            # DO NOT OVERWRITE! Preserve existing canonical fact
            return

        # Record audit history before overwriting
        session.add(
            VerificationHistory(
                scholarship_id=opp.id,
                field_name=field_name,
                old_value=curr_val,
                new_value=candidate_val,
                old_evidence_url=opp.official_sources[0].url if opp.official_sources else None,
                old_evidence_quote=opp.official_sources[0].extracted_text_snippet if opp.official_sources else None,
                new_evidence_url=candidate_ev.source_url if candidate_ev else None,
                new_evidence_quote=candidate_ev.evidence_text if candidate_ev else None,
                decision="CANONICAL_UPDATE_VERIFIED",
                reason=f"Verified replacement for {field_name}.",
                changed_at=now,
            )
        )
        setattr(opp, field_name, candidate_val)
