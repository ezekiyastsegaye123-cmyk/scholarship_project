"""Application service for API operations connecting Database models to Phase 1 engines."""
from datetime import date, datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from scholarship_intelligence.api.schemas import (
    ApplicationRecordCreate,
    ApplicationRecordItem,
    ApplicationRecordUpdate,
    AuthResponse,
    ComparisonItem,
    ComparisonResponse,
    ComparisonSelectionItem,
    IngestionRunItem,
    IngestionSourceItem,
    OpportunityDetail,
    OpportunitySummary,
    PaginatedApplications,
    PaginatedOpportunities,
    PaginatedSavedOpportunities,
    PersistentComparisonResponse,
    PersistentProfileResponse,
    PersistentProfileUpdate,
    SavedOpportunityItem,
    StudentAccountItem,
    StudentProfileInput,
    VerificationHistoryItem,
)
from scholarship_intelligence.auth.security import (
    AuthenticationError,
    create_access_token,
    hash_password,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    ApplicationStatus,
    DeadlineType,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.ingestion.freshness import FreshnessClassifier
from scholarship_intelligence.models.application_record import ApplicationRecord
from scholarship_intelligence.models.comparison_selection import ComparisonSelection
from scholarship_intelligence.models.deadline import Deadline
from scholarship_intelligence.models.ingestion_run import IngestionRun
from scholarship_intelligence.models.ingestion_source import IngestionSource
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.provider import Provider
from scholarship_intelligence.models.saved_opportunity import SavedOpportunity
from scholarship_intelligence.models.student_account import StudentAccount
from scholarship_intelligence.models.student_profile import StudentProfile
from scholarship_intelligence.models.university import University
from scholarship_intelligence.models.verification_history import VerificationHistory
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult
from fastapi import HTTPException, status


class ApiService:
    """Bridges web requests to the database and Phase 1 intelligence engines."""

    def __init__(self):
        self.evaluator = EligibilityEvaluator()
        self.counselor = ScholarshipCounselorService()

    def _get_earliest_deadline(
        self, deadlines: List[Any], reference_date: Optional[date] = None
    ) -> Tuple[Optional[date], Optional[DeadlineType], str]:
        """Deterministically extracts the earliest active or upcoming deadline and status."""
        if not deadlines:
            return None, None, "UNKNOWN"

        ref = reference_date or date(2026, 11, 1)
        valid_deadlines = [d for d in deadlines if getattr(d, "deadline_date", None) is not None]
        if not valid_deadlines:
            return None, None, "UNKNOWN"

        # Sort by deadline date ascending
        sorted_deadlines = sorted(valid_deadlines, key=lambda d: d.deadline_date)
        
        # Check upcoming
        upcoming = [d for d in sorted_deadlines if d.deadline_date >= ref]
        if upcoming:
            earliest = upcoming[0]
            return earliest.deadline_date, getattr(earliest, "deadline_type", None), "UPCOMING"

        # All passed
        earliest = sorted_deadlines[-1]
        return earliest.deadline_date, getattr(earliest, "deadline_type", None), "PASSED"

    def _format_funding_summary(self, opp: ScholarshipOpportunity) -> Tuple[FundingClassification, str]:
        """Formats the funding classification and a truthful human summary."""
        award = getattr(opp, "award", None)
        if not award:
            return FundingClassification.UNKNOWN, "Funding terms not published by provider"

        classification = getattr(award, "classification", FundingClassification.UNKNOWN)
        if isinstance(classification, str):
            try:
                classification = FundingClassification(classification)
            except ValueError:
                classification = FundingClassification.UNKNOWN

        components = getattr(award, "funding_components", []) or []
        component_names = [getattr(c, "component_type", "COMPONENT") for c in components]

        if classification == FundingClassification.FULL_FUNDING:
            summary = "Full Funding (Tuition and comprehensive living support)"
        elif classification == FundingClassification.FULL_TUITION:
            summary = "Full Tuition Coverage (Excludes room & board)"
        elif classification == FundingClassification.PARTIAL_FUNDING:
            summary = f"Partial Aid Package ({', '.join(component_names) if component_names else 'stipend/fees'})"
        elif classification == FundingClassification.STIPEND_ONLY:
            summary = "Living Stipend Only"
        elif classification == FundingClassification.FEES_ONLY:
            summary = "Mandatory Fees Only"
        else:
            summary = "Funding details under provider review"

        return classification, summary

    def _get_primary_source_url(self, opp: ScholarshipOpportunity) -> Optional[str]:
        """Gets the official authoritative URL for the opportunity."""
        official_sources = getattr(opp, "official_sources", []) or []
        for src in official_sources:
            if getattr(src, "is_primary", False) and getattr(src, "url", None):
                return src.url
        if official_sources and getattr(official_sources[0], "url", None):
            return official_sources[0].url
        
        discovery_sources = getattr(opp, "discovery_sources", []) or []
        if discovery_sources and getattr(discovery_sources[0], "url", None):
            return discovery_sources[0].url
        return None

    def to_summary(
        self, opp: ScholarshipOpportunity, reference_date: Optional[date] = None
    ) -> OpportunitySummary:
        """Converts a ScholarshipOpportunity ORM model into a stable OpportunitySummary DTO."""
        earliest_dl, dl_type, dl_status = self._get_earliest_deadline(
            getattr(opp, "deadlines", []), reference_date=reference_date
        )
        funding_cls, funding_summary = self._format_funding_summary(opp)
        primary_url = self._get_primary_source_url(opp)

        raw_v_status = getattr(opp, "verification_status", VerificationState.UNVERIFIED.value)
        v_status = VerificationState(raw_v_status) if isinstance(raw_v_status, str) else raw_v_status

        ref_dt = (
            datetime.combine(reference_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            if reference_date
            else datetime(2026, 11, 1, tzinfo=timezone.utc)
        )
        freshness = FreshnessClassifier.classify(opp, reference_time=ref_dt)

        return OpportunitySummary(
            id=str(opp.id),
            title=opp.title,
            slug=opp.slug,
            provider_name=opp.provider.name if opp.provider else None,
            university_name=opp.university.name if opp.university else None,
            target_degree_level=opp.target_degree_level,
            destination_country=opp.destination_country,
            academic_cycle=opp.academic_cycle,
            verification_status=v_status,
            funding_classification=funding_cls,
            funding_summary=funding_summary,
            earliest_deadline=earliest_dl,
            deadline_type=dl_type,
            deadline_status=dl_status,
            international_students_allowed=TriState(opp.international_students_allowed)
            if isinstance(opp.international_students_allowed, str)
            else opp.international_students_allowed,
            requires_sat=TriState(opp.requires_sat) if isinstance(opp.requires_sat, str) else opp.requires_sat,
            requires_act=TriState(opp.requires_act) if isinstance(opp.requires_act, str) else opp.requires_act,
            financial_need_required=TriState(opp.financial_need_required)
            if isinstance(opp.financial_need_required, str)
            else opp.financial_need_required,
            primary_source_url=primary_url,
            freshness_level=freshness.level.value,
            freshness_message=freshness.message,
            last_crawled_at=freshness.last_crawled_at,
        )

    def _build_opportunity_summary(
        self, opp: Optional[ScholarshipOpportunity], reference_date: Optional[date] = None
    ) -> Optional[OpportunitySummary]:
        """Convenience wrapper to safely convert an opportunity to OpportunitySummary."""
        if opp is None:
            return None
        return self.to_summary(opp, reference_date=reference_date)

    def list_opportunities(
        self,
        session: Session,
        search: Optional[str] = None,
        degree_level: Optional[str] = None,
        international_allowed: Optional[str] = None,
        provider: Optional[str] = None,
        university: Optional[str] = None,
        funding_type: Optional[str] = None,
        verification_status: Optional[str] = None,
        deadline_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        order_by: str = "deadline",
        reference_date: Optional[date] = None,
    ) -> PaginatedOpportunities:
        """Searches, filters, and paginates opportunities with deterministic ordering."""
        query = session.query(ScholarshipOpportunity).options(
            joinedload(ScholarshipOpportunity.provider),
            joinedload(ScholarshipOpportunity.university),
            joinedload(ScholarshipOpportunity.award).selectinload(getattr(ScholarshipOpportunity, "award").property.mapper.class_.funding_components),
            selectinload(ScholarshipOpportunity.deadlines),
            selectinload(ScholarshipOpportunity.official_sources),
            selectinload(ScholarshipOpportunity.discovery_sources),
        )

        # 1. Text Search across Title, Description, University, Provider
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.outerjoin(ScholarshipOpportunity.provider).outerjoin(ScholarshipOpportunity.university).filter(
                or_(
                    ScholarshipOpportunity.title.ilike(term),
                    ScholarshipOpportunity.description.ilike(term),
                    Provider.name.ilike(term),
                    University.name.ilike(term),
                )
            )

        # 2. Filters
        if degree_level:
            query = query.filter(ScholarshipOpportunity.target_degree_level == degree_level.strip())
        if international_allowed:
            query = query.filter(ScholarshipOpportunity.international_students_allowed == international_allowed.strip())
        if provider:
            query = query.join(ScholarshipOpportunity.provider).filter(Provider.name.ilike(f"%{provider.strip()}%"))
        if university:
            query = query.join(ScholarshipOpportunity.university).filter(University.name.ilike(f"%{university.strip()}%"))
        if verification_status:
            query = query.filter(ScholarshipOpportunity.verification_status == verification_status.strip())

        all_matching = query.all()

        # 3. In-memory secondary filters for complex relations (funding_type, deadline_status)
        filtered: List[ScholarshipOpportunity] = []
        ref = reference_date or date(2026, 11, 1)

        for opp in all_matching:
            # Funding filter
            if funding_type:
                f_cls, _ = self._format_funding_summary(opp)
                if f_cls.value != funding_type.strip():
                    continue

            # Deadline status filter
            if deadline_status:
                _, _, dl_stat = self._get_earliest_deadline(opp.deadlines, reference_date=ref)
                if dl_stat != deadline_status.strip().upper():
                    continue

            filtered.append(opp)

        # 4. Deterministic Ordering
        if order_by == "title":
            filtered.sort(key=lambda o: o.title.lower())
        elif order_by == "university":
            filtered.sort(key=lambda o: (o.university.name.lower() if o.university else "", o.title.lower()))
        else:
            # Default "deadline": upcoming deadline asc, then passed, then no deadline, then title
            def deadline_sort_key(o: ScholarshipOpportunity):
                dl_date, _, stat = self._get_earliest_deadline(o.deadlines, reference_date=ref)
                priority = 0 if stat == "UPCOMING" else (1 if stat == "PASSED" else 2)
                dl_val = dl_date or date(9999, 12, 31)
                return (priority, dl_val, o.title.lower())

            filtered.sort(key=deadline_sort_key)

        total = len(filtered)
        total_pages = max(1, math.ceil(total / page_size))
        current_page = min(max(1, page), total_pages) if total > 0 else 1
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paged_opps = filtered[start_idx:end_idx]

        items = [self.to_summary(o, reference_date=ref) for o in paged_opps]

        return PaginatedOpportunities(
            items=items,
            total=total,
            page=current_page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_opportunity_detail(
        self, session: Session, opportunity_id: str, reference_date: Optional[date] = None
    ) -> OpportunityDetail:
        """Fetches full opportunity details including all verified facts and evidence references."""
        opp = (
            session.query(ScholarshipOpportunity)
            .options(
                joinedload(ScholarshipOpportunity.provider),
                joinedload(ScholarshipOpportunity.university),
                joinedload(ScholarshipOpportunity.award).selectinload(getattr(ScholarshipOpportunity, "award").property.mapper.class_.funding_components),
                selectinload(ScholarshipOpportunity.deadlines),
                selectinload(ScholarshipOpportunity.eligibility_rules),
                selectinload(ScholarshipOpportunity.requirements),
                selectinload(ScholarshipOpportunity.application_requirements),
                selectinload(ScholarshipOpportunity.official_sources),
                selectinload(ScholarshipOpportunity.discovery_sources),
                selectinload(ScholarshipOpportunity.verification_records),
                selectinload(ScholarshipOpportunity.conflict_records),
                selectinload(ScholarshipOpportunity.verification_histories),
            )
            .filter(ScholarshipOpportunity.id == opportunity_id)
            .first()
        )

        if not opp:
            raise ValueError(f"Scholarship opportunity with ID '{opportunity_id}' not found.")

        ref = reference_date or date(2026, 11, 1)
        summary = self.to_summary(opp, reference_date=ref)

        # Decompose award details
        award_dict = None
        if opp.award:
            components_list = []
            for c in getattr(opp.award, "funding_components", []) or []:
                components_list.append({
                    "id": str(c.id),
                    "component_type": str(c.component_type),
                    "amount_min": float(c.amount_min) if c.amount_min is not None else None,
                    "amount_max": float(c.amount_max) if c.amount_max is not None else None,
                    "currency": c.currency,
                    "amount_period": str(c.amount_period) if c.amount_period else None,
                    "percentage_tuition": float(c.percentage_tuition) if c.percentage_tuition is not None else None,
                    "description": c.description,
                    "source_evidence_snippet": c.source_evidence_snippet,
                })
            award_dict = {
                "id": str(opp.award.id),
                "funding_classification": str(opp.award.funding_classification),
                "title": opp.award.title,
                "is_renewable": str(opp.award.is_renewable),
                "renewal_criteria": opp.award.renewal_criteria,
                "estimated_annual_value_usd": float(opp.award.estimated_annual_value_usd) if opp.award.estimated_annual_value_usd is not None else None,
                "components": components_list,
            }

        # Format deadlines
        deadlines_list = [
            {
                "id": str(d.id),
                "deadline_date": d.deadline_date.isoformat() if d.deadline_date else None,
                "deadline_type": str(d.deadline_type),
                "is_exact_date": bool(d.is_exact_date),
                "timezone": d.timezone,
                "academic_cycle": d.academic_cycle,
                "varies_by_program": bool(d.varies_by_program),
                "context_description": d.context_description,
                "source_evidence_snippet": d.source_evidence_snippet,
            }
            for d in (opp.deadlines or [])
        ]

        # Format eligibility rules
        rules_list = [
            {
                "id": str(r.id),
                "rule_id": r.rule_id,
                "kind": str(r.kind),
                "expression_json": r.expression_json,
                "description": r.description,
                "source_evidence_snippet": r.source_evidence_snippet,
                "is_verified": bool(r.is_verified),
            }
            for r in (opp.eligibility_rules or [])
        ]

        # Format requirements
        reqs_list = [
            {
                "id": str(rq.id),
                "requirement_type": str(rq.requirement_type),
                "kind": str(rq.kind),
                "name": rq.name,
                "description": rq.description,
                "source_evidence_snippet": rq.source_evidence_snippet,
            }
            for rq in (opp.requirements or [])
        ]

        # Format application requirements
        app_reqs_list = [
            {
                "id": str(ar.id),
                "requirement_type": str(ar.requirement_type),
                "kind": str(ar.kind),
                "title": ar.title,
                "description": ar.description,
                "instructions": ar.instructions,
                "submission_format": ar.submission_format,
                "source_evidence_snippet": ar.source_evidence_snippet,
            }
            for ar in (opp.application_requirements or [])
        ]

        # Format sources
        official_list = [
            {
                "id": str(s.id),
                "url": s.url,
                "source_domain": s.source_domain,
                "authority_tier": str(s.authority_tier),
                "is_primary": bool(s.is_primary),
                "page_title": s.page_title,
                "extracted_text_snippet": s.extracted_text_snippet,
                "last_crawled_at": s.last_crawled_at.isoformat() if s.last_crawled_at else None,
                "last_http_status": s.last_http_status,
            }
            for s in (opp.official_sources or [])
        ]

        discovery_list = [
            {
                "id": str(ds.id),
                "url": ds.url,
                "source_name": ds.source_name,
                "authority_tier": str(ds.authority_tier),
                "discovery_notes": ds.discovery_notes,
                "discovered_at": ds.discovered_at.isoformat() if ds.discovered_at else None,
            }
            for ds in (opp.discovery_sources or [])
        ]

        verif_records_list = [
            {
                "id": str(vr.id),
                "verification_state": str(vr.verification_state),
                "verifier_identity": vr.verifier_identity,
                "verification_method": vr.verification_method,
                "evidence_url": vr.evidence_url,
                "evidence_quote": vr.evidence_quote,
                "notes": vr.notes,
                "verified_at": vr.verified_at.isoformat() if vr.verified_at else None,
            }
            for vr in (opp.verification_records or [])
        ]

        conflicts_list = [
            {
                "id": str(cr.id),
                "field_name": cr.field_name,
                "source_a_value": cr.source_a_value,
                "source_a_url": cr.source_a_url,
                "source_b_value": cr.source_b_value,
                "source_b_url": cr.source_b_url,
                "source_a_tier": cr.source_a_tier,
                "source_b_tier": cr.source_b_tier,
                "source_a_evidence": cr.source_a_evidence,
                "source_b_evidence": cr.source_b_evidence,
                "resolution_status": str(cr.resolution_status),
                "resolution_notes": cr.resolution_notes,
                "resolved_at": cr.resolved_at.isoformat() if cr.resolved_at else None,
                "recorded_at": cr.recorded_at.isoformat() if cr.recorded_at else None,
            }
            for cr in (opp.conflict_records or [])
        ]

        history_list = [
            {
                "id": str(vh.id),
                "scholarship_id": str(vh.scholarship_id),
                "field_name": vh.field_name,
                "old_value": vh.old_value,
                "new_value": vh.new_value,
                "old_evidence_url": vh.old_evidence_url,
                "old_evidence_quote": vh.old_evidence_quote,
                "new_evidence_url": vh.new_evidence_url,
                "new_evidence_quote": vh.new_evidence_quote,
                "decision": vh.decision,
                "reason": vh.reason,
                "changed_at": vh.changed_at.isoformat() if vh.changed_at else None,
            }
            for vh in sorted(
                opp.verification_histories or [],
                key=lambda h: h.changed_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
        ]

        return OpportunityDetail(
            **summary.model_dump(),
            description=opp.description,
            varies_by_program=bool(opp.varies_by_program),
            requires_css_profile=TriState(opp.requires_css_profile)
            if isinstance(opp.requires_css_profile, str)
            else opp.requires_css_profile,
            fingerprint_sha256=opp.fingerprint_sha256,
            award_details=award_dict,
            deadlines=deadlines_list,
            eligibility_rules=rules_list,
            requirements=reqs_list,
            application_requirements=app_reqs_list,
            official_sources=official_list,
            discovery_sources=discovery_list,
            verification_records=verif_records_list,
            conflict_records=conflicts_list,
            verification_histories=history_list,
        )

    def evaluate_opportunity(
        self,
        session: Session,
        opportunity_id: str,
        profile: StudentProfileInput,
        target_academic_cycle: str = "2026-2027",
        allow_partially_verified: bool = False,
        evaluated_at: Optional[datetime] = None,
    ) -> EligibilityEvaluationResult:
        """Invokes the Phase 1 EligibilityEvaluator on an opportunity."""
        opp = (
            session.query(ScholarshipOpportunity)
            .options(selectinload(ScholarshipOpportunity.eligibility_rules))
            .filter(ScholarshipOpportunity.id == opportunity_id)
            .first()
        )
        if not opp:
            raise ValueError(f"Scholarship opportunity with ID '{opportunity_id}' not found.")

        return self.evaluator.evaluate_opportunity(
            opportunity=opp,
            student_profile=profile.model_dump(),
            target_academic_cycle=target_academic_cycle,
            allow_partially_verified=allow_partially_verified,
            evaluated_at=evaluated_at,
        )

    def counsel_opportunity(
        self,
        session: Session,
        opportunity_id: str,
        profile: StudentProfileInput,
        target_academic_cycle: str = "2026-2027",
        reference_date: Optional[date] = None,
        evaluated_at: Optional[datetime] = None,
    ) -> CounselorAssessmentResult:
        """Invokes the Phase 1 ScholarshipCounselorService on an opportunity."""
        opp = (
            session.query(ScholarshipOpportunity)
            .options(
                joinedload(ScholarshipOpportunity.award).selectinload(getattr(ScholarshipOpportunity, "award").property.mapper.class_.funding_components),
                selectinload(ScholarshipOpportunity.deadlines),
                selectinload(ScholarshipOpportunity.eligibility_rules),
                selectinload(ScholarshipOpportunity.requirements),
                selectinload(ScholarshipOpportunity.application_requirements),
                selectinload(ScholarshipOpportunity.official_sources),
                selectinload(ScholarshipOpportunity.verification_records),
                selectinload(ScholarshipOpportunity.conflict_records),
            )
            .filter(ScholarshipOpportunity.id == opportunity_id)
            .first()
        )
        if not opp:
            raise ValueError(f"Scholarship opportunity with ID '{opportunity_id}' not found.")

        # 1. First run eligibility evaluator
        elig_res = self.evaluator.evaluate_opportunity(
            opportunity=opp,
            student_profile=profile.model_dump(),
            target_academic_cycle=target_academic_cycle,
            allow_partially_verified=True,
            evaluated_at=evaluated_at,
        )

        ref = reference_date or date(2026, 11, 1)

        # 2. Run counselor service
        return self.counselor.assess_opportunity(
            student_profile=profile.model_dump(),
            opportunity=opp,
            eligibility_result=elig_res,
            reference_date=ref,
            evaluated_at=evaluated_at,
        )

    def compare_opportunities(
        self,
        session: Session,
        opportunity_ids: List[str],
        profile: Optional[StudentProfileInput] = None,
        target_academic_cycle: str = "2026-2027",
        reference_date: Optional[date] = None,
        evaluated_at: Optional[datetime] = None,
    ) -> ComparisonResponse:
        """Compares selected opportunities across transparent dimensions without composite scoring."""
        ref = reference_date or date(2026, 11, 1)
        items: List[ComparisonItem] = []

        for opp_id in opportunity_ids:
            opp = (
                session.query(ScholarshipOpportunity)
                .options(
                    joinedload(ScholarshipOpportunity.provider),
                    joinedload(ScholarshipOpportunity.university),
                    joinedload(ScholarshipOpportunity.award).selectinload(getattr(ScholarshipOpportunity, "award").property.mapper.class_.funding_components),
                    selectinload(ScholarshipOpportunity.deadlines),
                    selectinload(ScholarshipOpportunity.eligibility_rules),
                    selectinload(ScholarshipOpportunity.requirements),
                    selectinload(ScholarshipOpportunity.application_requirements),
                    selectinload(ScholarshipOpportunity.official_sources),
                )
                .filter(ScholarshipOpportunity.id == opp_id)
                .first()
            )
            if not opp:
                continue

            earliest_dl, _, dl_stat = self._get_earliest_deadline(opp.deadlines, reference_date=ref)
            funding_cls, funding_summary = self._format_funding_summary(opp)
            primary_url = self._get_primary_source_url(opp)
            raw_v_status = getattr(opp, "verification_status", VerificationState.UNVERIFIED.value)
            v_status = VerificationState(raw_v_status) if isinstance(raw_v_status, str) else raw_v_status

            elig_status = None
            elig_summary = None
            acad_align = None
            geo_align = None
            prog_align = None
            test_ready = None
            app_ready = None

            if profile:
                counsel_res = self.counsel_opportunity(
                    session=session,
                    opportunity_id=opp_id,
                    profile=profile,
                    target_academic_cycle=target_academic_cycle,
                    reference_date=ref,
                    evaluated_at=evaluated_at,
                )
                elig_status = counsel_res.eligibility_status.value
                elig_summary = counsel_res.eligibility_summary
                acad_align = counsel_res.academic_alignment.level.value
                geo_align = counsel_res.geographic_alignment.level.value
                prog_align = counsel_res.program_alignment.level.value
                test_ready = counsel_res.testing_readiness.level.value
                app_ready = counsel_res.application_readiness.level.value

            items.append(
                ComparisonItem(
                    opportunity_id=str(opp.id),
                    opportunity_title=opp.title,
                    provider_name=opp.provider.name if opp.provider else None,
                    university_name=opp.university.name if opp.university else None,
                    verification_status=v_status,
                    funding_classification=funding_cls,
                    funding_summary=funding_summary,
                    earliest_deadline=earliest_dl,
                    deadline_status=dl_stat,
                    primary_source_url=primary_url,
                    eligibility_status=elig_status,
                    eligibility_summary=elig_summary,
                    academic_alignment=acad_align,
                    geographic_alignment=geo_align,
                    program_alignment=prog_align,
                    testing_readiness=test_ready,
                    application_readiness=app_ready,
                )
            )

        return ComparisonResponse(
            items=items,
            ordering_rule="Preserves user selection order; zero composite match score or arbitrary ranking algorithm",
            total_compared=len(items),
        )

    def get_verification_history(self, session: Session, opportunity_id: str) -> List[VerificationHistoryItem]:
        """Fetches complete audit trail of fact modifications for an opportunity."""
        histories = (
            session.query(VerificationHistory)
            .filter(VerificationHistory.scholarship_id == opportunity_id)
            .order_by(VerificationHistory.changed_at.desc())
            .all()
        )
        return [
            VerificationHistoryItem(
                id=str(h.id),
                scholarship_id=str(h.scholarship_id),
                field_name=h.field_name,
                old_value=h.old_value,
                new_value=h.new_value,
                old_evidence_url=h.old_evidence_url,
                old_evidence_quote=h.old_evidence_quote,
                new_evidence_url=h.new_evidence_url,
                new_evidence_quote=h.new_evidence_quote,
                decision=h.decision,
                reason=h.reason,
                changed_at=h.changed_at,
            )
            for h in histories
        ]

    def list_ingestion_runs(self, session: Session, limit: int = 50) -> List[IngestionRunItem]:
        """Retrieves past ingestion execution runs with status and metrics."""
        runs = session.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit).all()
        return [
            IngestionRunItem(
                id=str(r.id),
                run_type=r.run_type,
                status=r.status,
                started_at=r.started_at,
                finished_at=r.finished_at,
                sources_attempted=r.sources_attempted,
                sources_succeeded=r.sources_succeeded,
                sources_failed=r.sources_failed,
                opportunities_scanned=r.opportunities_scanned,
                opportunities_updated=r.opportunities_updated,
                opportunities_created=r.opportunities_created,
                conflicts_detected=r.conflicts_detected,
                error_log_json=r.error_log_json,
                reference_time=r.reference_time,
            )
            for r in runs
        ]

    def list_ingestion_sources(self, session: Session) -> List[IngestionSourceItem]:
        """Retrieves all registered ingestion sources and their crawl statuses."""
        sources = session.query(IngestionSource).order_by(IngestionSource.name.asc()).all()
        return [
            IngestionSourceItem(
                id=str(s.id),
                name=s.name,
                url=s.url,
                source_domain=s.source_domain,
                authority_tier=s.authority_tier,
                is_active=s.is_active,
                fetch_interval_hours=s.fetch_interval_hours,
                last_crawled_at=s.last_crawled_at,
                last_content_sha256=s.last_content_sha256,
                last_http_status=s.last_http_status,
                failure_count=s.failure_count,
                description=s.description,
            )
            for s in sources
        ]

    # ==============================================================================
    # PHASE 4: ACCOUNTS & AUTHENTICATION
    # ==============================================================================

    def register_account(self, session: Session, email: str, password: str) -> AuthResponse:
        """Registers a new student account transactionally with initial profile."""
        try:
            norm_email = normalize_email(email)
            validate_password_strength(password)
        except AuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        existing = session.query(StudentAccount).filter(StudentAccount.email == norm_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        pwd_hash = hash_password(password)
        account = StudentAccount(
            email=norm_email,
            password_hash=pwd_hash,
            is_active=True,
        )
        session.add(account)
        session.flush()  # assign account.id

        # Create linked default student profile
        profile = StudentProfile(
            account_id=account.id,
            citizenship_country="UNKNOWN",
            residence_country="UNKNOWN",
            intended_degree_level="BACHELOR",
            intended_destination_country="US",
        )
        session.add(profile)
        session.commit()
        session.refresh(account)

        token, expires_at = create_access_token(account_id=account.id, email=account.email)
        return AuthResponse(
            account=StudentAccountItem(
                id=account.id,
                email=account.email,
                is_active=account.is_active,
                created_at=account.created_at,
                last_login_at=account.last_login_at,
                has_profile=True,
            ),
            token=token,
            expires_at=expires_at,
        )

    def login_account(self, session: Session, email: str, password: str) -> AuthResponse:
        """Authenticates student credentials and issues access session token."""
        try:
            norm_email = normalize_email(email)
        except AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        account = session.query(StudentAccount).filter(StudentAccount.email == norm_email).first()
        if not account or not verify_password(password, account.password_hash) or not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        account.last_login_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(account)

        token, expires_at = create_access_token(account_id=account.id, email=account.email)
        return AuthResponse(
            account=StudentAccountItem(
                id=account.id,
                email=account.email,
                is_active=account.is_active,
                created_at=account.created_at,
                last_login_at=account.last_login_at,
                has_profile=account.profile is not None,
            ),
            token=token,
            expires_at=expires_at,
        )

    def get_me(self, session: Session, account: StudentAccount) -> StudentAccountItem:
        """Returns safe representation of currently authenticated student account."""
        return StudentAccountItem(
            id=account.id,
            email=account.email,
            is_active=account.is_active,
            created_at=account.created_at,
            last_login_at=account.last_login_at,
            has_profile=account.profile is not None,
        )

    # ==============================================================================
    # PHASE 4: PERSISTENT STUDENT PROFILE
    # ==============================================================================

    def get_persistent_profile(self, session: Session, account_id: str) -> PersistentProfileResponse:
        """Retrieves persistent profile owned by the authenticated student account."""
        profile = session.query(StudentProfile).filter(StudentProfile.account_id == account_id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        return PersistentProfileResponse(
            id=profile.id,
            account_id=profile.account_id,
            citizenship_country=profile.citizenship_country,
            residence_country=profile.residence_country,
            intended_degree_level=profile.intended_degree_level,
            intended_destination_country=profile.intended_destination_country,
            gpa=profile.gpa,
            gpa_scale=profile.gpa_scale,
            intended_major=profile.intended_major,
            english_test_type=profile.english_test_type,
            english_test_score=profile.english_test_score,
            sat_score=profile.sat_score,
            act_score=profile.act_score,
            financial_need_tier=profile.financial_need_tier,
            academic_achievements=profile.academic_achievements or [],
            extracurricular_activities=profile.extracurricular_activities or [],
            interests=profile.interests or [],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def update_persistent_profile(
        self,
        session: Session,
        account_id: str,
        update: PersistentProfileUpdate,
    ) -> PersistentProfileResponse:
        """Updates persistent profile fields owned strictly by authenticated student."""
        profile = session.query(StudentProfile).filter(StudentProfile.account_id == account_id).first()
        if not profile:
            profile = StudentProfile(
                account_id=account_id,
                citizenship_country="UNKNOWN",
                residence_country="UNKNOWN",
                intended_degree_level="BACHELOR",
                intended_destination_country="US",
            )
            session.add(profile)
            session.flush()

        update_dict = update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(profile, field) and field not in ("id", "account_id", "created_at"):
                setattr(profile, field, value)

        session.commit()
        session.refresh(profile)

        return self.get_persistent_profile(session, account_id)

    # ==============================================================================
    # PHASE 4: SAVED SCHOLARSHIPS
    # ==============================================================================

    def save_opportunity(self, session: Session, account_id: str, opportunity_id: str) -> SavedOpportunityItem:
        """Saves a scholarship opportunity reference idempotently for the student."""
        opp = session.query(ScholarshipOpportunity).filter(ScholarshipOpportunity.id == opportunity_id).first()
        if not opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship opportunity not found.")

        existing = session.query(SavedOpportunity).filter(
            SavedOpportunity.student_account_id == account_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        ).first()

        if existing:
            return SavedOpportunityItem(
                id=existing.id,
                student_account_id=existing.student_account_id,
                opportunity_id=existing.opportunity_id,
                saved_at=existing.created_at,
                opportunity=self._build_opportunity_summary(opp),
            )

        saved = SavedOpportunity(
            student_account_id=account_id,
            opportunity_id=opportunity_id,
        )
        session.add(saved)
        session.commit()
        session.refresh(saved)

        return SavedOpportunityItem(
            id=saved.id,
            student_account_id=saved.student_account_id,
            opportunity_id=saved.opportunity_id,
            saved_at=saved.created_at,
            opportunity=self._build_opportunity_summary(opp),
        )

    def unsave_opportunity(self, session: Session, account_id: str, opportunity_id: str) -> bool:
        """Removes a saved scholarship opportunity reference."""
        saved = session.query(SavedOpportunity).filter(
            SavedOpportunity.student_account_id == account_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        ).first()

        if not saved:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity is not in saved list.")

        session.delete(saved)
        session.commit()
        return True

    def list_saved_opportunities(
        self,
        session: Session,
        account_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedSavedOpportunities:
        """Retrieves paginated saved opportunities with current canonical intelligence."""
        query = (
            session.query(SavedOpportunity)
            .filter(SavedOpportunity.student_account_id == account_id)
            .order_by(SavedOpportunity.created_at.desc())
        )
        total = query.count()
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items = [
            SavedOpportunityItem(
                id=r.id,
                student_account_id=r.student_account_id,
                opportunity_id=r.opportunity_id,
                saved_at=r.created_at,
                opportunity=self._build_opportunity_summary(r.opportunity),
            )
            for r in records
        ]
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaginatedSavedOpportunities(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ==============================================================================
    # PHASE 4: APPLICATION TRACKING
    # ==============================================================================

    def create_application(
        self,
        session: Session,
        account_id: str,
        data: ApplicationRecordCreate,
    ) -> ApplicationRecordItem:
        """Creates an application tracking record for an opportunity."""
        opp = session.query(ScholarshipOpportunity).filter(ScholarshipOpportunity.id == data.opportunity_id).first()
        if not opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship opportunity not found.")

        # Check valid status enum
        valid_statuses = {s.value for s in ApplicationStatus}
        if data.status not in valid_statuses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid application status '{data.status}'.")

        existing = session.query(ApplicationRecord).filter(
            ApplicationRecord.student_account_id == account_id,
            ApplicationRecord.opportunity_id == data.opportunity_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An application tracker record already exists for this scholarship.",
            )

        app_rec = ApplicationRecord(
            student_account_id=account_id,
            opportunity_id=data.opportunity_id,
            status=data.status,
            student_notes=data.student_notes,
            submitted_at=data.submitted_at,
        )
        session.add(app_rec)
        session.commit()
        session.refresh(app_rec)

        return ApplicationRecordItem(
            id=app_rec.id,
            student_account_id=app_rec.student_account_id,
            opportunity_id=app_rec.opportunity_id,
            status=app_rec.status,
            student_notes=app_rec.student_notes,
            submitted_at=app_rec.submitted_at,
            created_at=app_rec.created_at,
            updated_at=app_rec.updated_at,
            opportunity=self._build_opportunity_summary(opp),
        )

    def get_application(self, session: Session, account_id: str, application_id: str) -> ApplicationRecordItem:
        """Retrieves a single application tracking record with strict ownership check."""
        app_rec = session.query(ApplicationRecord).filter(
            ApplicationRecord.id == application_id,
            ApplicationRecord.student_account_id == account_id,
        ).first()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

        return ApplicationRecordItem(
            id=app_rec.id,
            student_account_id=app_rec.student_account_id,
            opportunity_id=app_rec.opportunity_id,
            status=app_rec.status,
            student_notes=app_rec.student_notes,
            submitted_at=app_rec.submitted_at,
            created_at=app_rec.created_at,
            updated_at=app_rec.updated_at,
            opportunity=self._build_opportunity_summary(app_rec.opportunity),
        )

    def update_application(
        self,
        session: Session,
        account_id: str,
        application_id: str,
        update: ApplicationRecordUpdate,
    ) -> ApplicationRecordItem:
        """Updates an application tracking record with strict ownership check."""
        app_rec = session.query(ApplicationRecord).filter(
            ApplicationRecord.id == application_id,
            ApplicationRecord.student_account_id == account_id,
        ).first()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

        if update.status is not None:
            valid_statuses = {s.value for s in ApplicationStatus}
            if update.status not in valid_statuses:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid application status '{update.status}'.")
            app_rec.status = update.status

        if update.student_notes is not None:
            app_rec.student_notes = update.student_notes

        if update.submitted_at is not None:
            app_rec.submitted_at = update.submitted_at

        session.commit()
        session.refresh(app_rec)

        return ApplicationRecordItem(
            id=app_rec.id,
            student_account_id=app_rec.student_account_id,
            opportunity_id=app_rec.opportunity_id,
            status=app_rec.status,
            student_notes=app_rec.student_notes,
            submitted_at=app_rec.submitted_at,
            created_at=app_rec.created_at,
            updated_at=app_rec.updated_at,
            opportunity=self._build_opportunity_summary(app_rec.opportunity),
        )

    def delete_application(self, session: Session, account_id: str, application_id: str) -> bool:
        """Deletes an application tracking record with strict ownership check."""
        app_rec = session.query(ApplicationRecord).filter(
            ApplicationRecord.id == application_id,
            ApplicationRecord.student_account_id == account_id,
        ).first()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

        session.delete(app_rec)
        session.commit()
        return True

    def list_applications(
        self,
        session: Session,
        account_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedApplications:
        """Retrieves paginated application tracking records with current canonical intelligence."""
        query = (
            session.query(ApplicationRecord)
            .filter(ApplicationRecord.student_account_id == account_id)
            .order_by(ApplicationRecord.updated_at.desc())
        )
        total = query.count()
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items = [
            ApplicationRecordItem(
                id=r.id,
                student_account_id=r.student_account_id,
                opportunity_id=r.opportunity_id,
                status=r.status,
                student_notes=r.student_notes,
                submitted_at=r.submitted_at,
                created_at=r.created_at,
                updated_at=r.updated_at,
                opportunity=self._build_opportunity_summary(r.opportunity),
            )
            for r in records
        ]
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaginatedApplications(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ==============================================================================
    # PHASE 4: PERSISTENT COMPARISON
    # ==============================================================================

    def add_comparison_selection(
        self,
        session: Session,
        account_id: str,
        opportunity_id: str,
    ) -> PersistentComparisonResponse:
        """Adds opportunity to persistent comparison set up to MAX_COMPARE = 4."""
        opp = session.query(ScholarshipOpportunity).filter(ScholarshipOpportunity.id == opportunity_id).first()
        if not opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship opportunity not found.")

        existing = session.query(ComparisonSelection).filter(
            ComparisonSelection.student_account_id == account_id,
            ComparisonSelection.opportunity_id == opportunity_id,
        ).first()

        if existing:
            return self.list_comparison_selections(session, account_id)

        count = session.query(ComparisonSelection).filter(ComparisonSelection.student_account_id == account_id).count()
        if count >= 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can compare a maximum of 4 scholarships simultaneously.",
            )

        selection = ComparisonSelection(
            student_account_id=account_id,
            opportunity_id=opportunity_id,
        )
        session.add(selection)
        session.commit()

        return self.list_comparison_selections(session, account_id)

    def remove_comparison_selection(
        self,
        session: Session,
        account_id: str,
        opportunity_id: str,
    ) -> PersistentComparisonResponse:
        """Removes an opportunity from persistent comparison set."""
        existing = session.query(ComparisonSelection).filter(
            ComparisonSelection.student_account_id == account_id,
            ComparisonSelection.opportunity_id == opportunity_id,
        ).first()

        if existing:
            session.delete(existing)
            session.commit()

        return self.list_comparison_selections(session, account_id)

    def list_comparison_selections(
        self,
        session: Session,
        account_id: str,
    ) -> PersistentComparisonResponse:
        """Lists all active comparison selections for the student."""
        selections = (
            session.query(ComparisonSelection)
            .filter(ComparisonSelection.student_account_id == account_id)
            .order_by(ComparisonSelection.created_at.asc())
            .all()
        )
        items = [
            ComparisonSelectionItem(
                id=s.id,
                opportunity_id=s.opportunity_id,
                created_at=s.created_at,
                opportunity=self._build_opportunity_summary(s.opportunity),
            )
            for s in selections
        ]
        return PersistentComparisonResponse(
            items=items,
            count=len(items),
            max_allowed=4,
        )

    def clear_comparison_selections(
        self,
        session: Session,
        account_id: str,
    ) -> PersistentComparisonResponse:
        """Clears all comparison selections for the student."""
        session.query(ComparisonSelection).filter(ComparisonSelection.student_account_id == account_id).delete()
        session.commit()
        return PersistentComparisonResponse(items=[], count=0, max_allowed=4)

