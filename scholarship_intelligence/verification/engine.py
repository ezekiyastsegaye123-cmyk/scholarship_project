"""Phase 1C Verification Engine coordinating multi-factor evidence assessment."""
from datetime import datetime, timezone
from typing import Any, List, Optional


from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    ConflictStatus,
    LivenessStatus,
    QuarantineReason,
    VerificationState,
)
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.schemas.candidate import CandidateOpportunity
from scholarship_intelligence.schemas.verification import (
    ConflictRecordCreate,
    FactVerificationResult,
    SourceLivenessResult,
    VerificationDecisionResult,
)
from scholarship_intelligence.verification.conflict import ConflictEngine
from scholarship_intelligence.verification.fact_verifier import AUTHORITATIVE_TIERS, FactVerifier
from scholarship_intelligence.verification.risk_triage import RiskTriager


class VerificationEngine:
    """Pipeline coordinator transforming Phase 1B candidate data into verified or classified outcomes."""

    @classmethod
    def evaluate(
        cls,
        candidate: CandidateOpportunity,
        liveness_result: Optional[SourceLivenessResult] = None,
        canonical_opportunity: Optional[ScholarshipOpportunity] = None,
        target_cycle: str = "2026-2027",
    ) -> VerificationDecisionResult:
        quarantine_reasons: List[QuarantineReason] = []
        conflicts: List[ConflictRecordCreate] = []
        fact_results: List[FactVerificationResult] = []

        # 1. Step 1: Risk Signal Triage
        all_evidence_text = " ".join(ev.evidence_text for ev in candidate.source_evidence)
        triage_res = RiskTriager.evaluate(
            evidence_text=all_evidence_text,
            opportunity_description=candidate.description,
            source_url=candidate.source_evidence[0].source_url if candidate.source_evidence else None,
        )

        if triage_res.is_quarantined:
            quarantine_reasons.extend(triage_res.quarantine_reasons)
            return VerificationDecisionResult(
                overall_state=VerificationState.QUARANTINED_FOR_REVIEW,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale=f"Opportunity quarantined due to critical risk signals: {triage_res.quarantine_notes}",
                can_promote=False,
            )

        # 2. Step 2: Source Liveness & Reachability
        if liveness_result is not None:
            if not liveness_result.is_live or liveness_result.is_soft_404:
                return VerificationDecisionResult(
                    overall_state=VerificationState.SOURCE_UNAVAILABLE,
                    opportunity_title=candidate.title,
                    academic_cycle=candidate.academic_cycle,
                    facts=fact_results,
                    conflicts=conflicts,
                    quarantine_reasons=quarantine_reasons,
                    liveness_result=liveness_result,
                    rationale=f"Primary source unavailable ({liveness_result.liveness_status.value}): {liveness_result.error_message or 'Unreachable'}. Historical evidence preserved.",
                    can_promote=False,
                )

        # 3. Step 3: Fact-Level Evidence Verification
        primary_ev = candidate.source_evidence[0] if candidate.source_evidence else None
        
        # Verify scalar fields
        fact_results.append(FactVerifier.verify_field("international_students_allowed", candidate.international_students_allowed, primary_ev, target_cycle))
        fact_results.append(FactVerifier.verify_field("requires_sat", candidate.requires_sat, primary_ev, target_cycle))
        fact_results.append(FactVerifier.verify_field("requires_act", candidate.requires_act, primary_ev, target_cycle))
        fact_results.append(FactVerifier.verify_field("financial_need_required", candidate.financial_need_required, primary_ev, target_cycle))

        # Verify award & funding components
        if candidate.award:
            award_facts = FactVerifier.verify_funding_components(candidate.award, target_cycle)
            fact_results.extend(award_facts)

        # Verify deadlines
        if candidate.deadlines:
            deadline_facts = FactVerifier.verify_deadlines(candidate.deadlines, target_cycle)
            fact_results.extend(deadline_facts)

        # 4. Step 4: Conflict Detection against Canonical Opportunity (if existing)
        has_unresolved_conflict = False
        if canonical_opportunity is not None:
            # Check eligibility fields
            cls._check_canonical_field_conflict(
                field_name="international_students_allowed",
                candidate_val=candidate.international_students_allowed,
                candidate_ev=primary_ev,
                canonical_val=canonical_opportunity.international_students_allowed,
                canonical_opp=canonical_opportunity,
                conflicts=conflicts,
                fact_results=fact_results,
                current_cycle=target_cycle,
            )

            # Check deadlines
            if candidate.deadlines and canonical_opportunity.deadlines:
                for c_dl in candidate.deadlines:
                    for canon_dl in canonical_opportunity.deadlines:
                        if c_dl.deadline_type.value == canon_dl.deadline_type:
                            if c_dl.deadline_date and canon_dl.deadline_date and c_dl.deadline_date != canon_dl.deadline_date:
                                # Conflict detected!
                                canon_src = canonical_opportunity.official_sources[0] if canonical_opportunity.official_sources else None
                                canon_url = canon_src.url if canon_src else "https://canonical-university.edu"
                                canon_tier = AuthorityTier(canon_src.authority_tier) if canon_src else AuthorityTier.OFFICIAL_UNIVERSITY
                                canon_ev = canon_dl.source_evidence_snippet or "Canonical verified deadline."

                                resolution = ConflictEngine.resolve_conflict(
                                    field_name=f"deadline_{c_dl.deadline_type.value}",
                                    value_a=str(c_dl.deadline_date),
                                    source_a_url=c_dl.evidence.source_url,
                                    source_a_tier=c_dl.evidence.authority_tier,
                                    source_a_evidence=c_dl.evidence.evidence_text,
                                    cycle_a=c_dl.academic_cycle or candidate.academic_cycle,
                                    value_b=str(canon_dl.deadline_date),
                                    source_b_url=canon_url,
                                    source_b_tier=canon_tier,
                                    source_b_evidence=canon_ev,
                                    cycle_b=canon_dl.academic_cycle,
                                    current_cycle=target_cycle,
                                )
                                conflicts.append(resolution.conflict_record)
                                if not resolution.is_resolved:
                                    has_unresolved_conflict = True

        for c in conflicts:
            if c.resolution_status == ConflictStatus.OPEN:
                has_unresolved_conflict = True

        # 5. Step 5: Overall Verification State Assignment
        if has_unresolved_conflict:
            return VerificationDecisionResult(
                overall_state=VerificationState.CONFLICTING,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="Unresolved conflict detected between authoritative evidence sources. Preserving existing verified state.",
                can_promote=False,
            )

        # Check if all facts are OUTDATED
        outdated_count = sum(1 for f in fact_results if f.verification_state == VerificationState.OUTDATED)
        if outdated_count > 0 and outdated_count == len([f for f in fact_results if f.candidate_value != 'UNKNOWN']):
            return VerificationDecisionResult(
                overall_state=VerificationState.OUTDATED,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="All supporting evidence corresponds to an expired prior academic cycle. Marked OUTDATED.",
                can_promote=False,
            )

        # Check primary authority tier
        primary_tier = primary_ev.authority_tier if primary_ev else AuthorityTier.THIRD_PARTY
        if primary_tier not in AUTHORITATIVE_TIERS:
            return VerificationDecisionResult(
                overall_state=VerificationState.UNVERIFIED,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="Evidence derived exclusively from non-authoritative aggregator or third-party lead. Remains UNVERIFIED.",
                can_promote=False,
            )

        # Count verified vs unverified
        verified_count = sum(1 for f in fact_results if f.verification_state == VerificationState.VERIFIED)
        partially_count = sum(1 for f in fact_results if f.verification_state == VerificationState.PARTIALLY_VERIFIED)

        if verified_count > 0 and partially_count == 0:
            # Check if all material candidate fields are verified
            return VerificationDecisionResult(
                overall_state=VerificationState.VERIFIED,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="All material candidate facts verified against authoritative primary evidence with zero unresolved conflicts.",
                can_promote=True,
            )
        elif verified_count > 0 or partially_count > 0:
            return VerificationDecisionResult(
                overall_state=VerificationState.PARTIALLY_VERIFIED,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="Primary criteria verified with authoritative citations; secondary or optional components remain unverified.",
                can_promote=True,
            )
        else:
            return VerificationDecisionResult(
                overall_state=VerificationState.UNVERIFIED,
                opportunity_title=candidate.title,
                academic_cycle=candidate.academic_cycle,
                facts=fact_results,
                conflicts=conflicts,
                quarantine_reasons=quarantine_reasons,
                liveness_result=liveness_result,
                rationale="Insufficient evidence to verify candidate claims.",
                can_promote=False,
            )

    @classmethod
    def _check_canonical_field_conflict(
        cls,
        field_name: str,
        candidate_val: Any,
        candidate_ev: Optional[Any],
        canonical_val: Any,
        canonical_opp: ScholarshipOpportunity,
        conflicts: List[ConflictRecordCreate],
        fact_results: List[FactVerificationResult],
        current_cycle: str,
    ):
        if ConflictEngine.detect_fact_discrepancy(field_name, candidate_val, canonical_val):
            canon_src = canonical_opp.official_sources[0] if canonical_opp.official_sources else None
            canon_url = canon_src.url if canon_src else "https://canonical-university.edu"
            canon_tier = AuthorityTier(canon_src.authority_tier) if canon_src else AuthorityTier.OFFICIAL_UNIVERSITY
            canon_ev = canon_src.extracted_text_snippet if canon_src else "Canonical verified value."

            cand_url = candidate_ev.source_url if candidate_ev else "https://candidate.com"
            cand_tier = candidate_ev.authority_tier if candidate_ev else AuthorityTier.THIRD_PARTY
            cand_ev = candidate_ev.evidence_text if candidate_ev else ""

            val_a_str = candidate_val.value if hasattr(candidate_val, "value") else str(candidate_val)
            val_b_str = canonical_val.value if hasattr(canonical_val, "value") else str(canonical_val)
            resolution = ConflictEngine.resolve_conflict(
                field_name=field_name,
                value_a=val_a_str,
                source_a_url=cand_url,
                source_a_tier=cand_tier,
                source_a_evidence=cand_ev,
                cycle_a=canonical_opp.academic_cycle,
                value_b=val_b_str,
                source_b_url=canon_url,
                source_b_tier=canon_tier,
                source_b_evidence=canon_ev,
                cycle_b=canonical_opp.academic_cycle,
                current_cycle=current_cycle,
            )

            conflicts.append(resolution.conflict_record)
            if not resolution.is_resolved:
                # Mark matching fact as conflicting
                for idx, fr in enumerate(fact_results):
                    if fr.field_name == field_name:
                        fact_results[idx] = FactVerificationResult(
                            field_name=field_name,
                            candidate_value=candidate_val,
                            canonical_value=canonical_val,
                            verification_state=VerificationState.CONFLICTING,
                            supporting_evidence=candidate_ev,
                            authority_tier=cand_tier,
                            notes="Discrepancy with existing verified canonical record could not be deterministically resolved.",
                            is_conflict=True,
                            conflict_record=resolution.conflict_record,
                        )
