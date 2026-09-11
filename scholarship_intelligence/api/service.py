"""Application service for API operations connecting Database models to Phase 1 engines."""
from datetime import date, datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from scholarship_intelligence.api.schemas import (
    ComparisonItem,
    ComparisonResponse,
    OpportunityDetail,
    OpportunitySummary,
    PaginatedOpportunities,
    StudentProfileInput,
)
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.domain.enums import (
    DeadlineType,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.models.deadline import Deadline
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.provider import Provider
from scholarship_intelligence.models.university import University
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult


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
        )

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
