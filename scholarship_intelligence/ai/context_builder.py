"""Context builder for the AI Counselor.

Transforms Phase 1–4 deterministic outputs and institutional opportunity models
into a strictly bounded, privacy-sanitized CounselorContext DTO.

Invariants:
- All sensitive forbidden fields are rejected and never enter the context.
- UNKNOWN, CONFLICTING, and UNVERIFIED states are explicitly mapped.
- Zero numerical scores, rankings, or probabilities are computed or included.
- Execution is strictly deterministic.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from scholarship_intelligence.ai.schemas import (
    CounselorContext,
    EpistemicStatus,
    SourceCitation,
)
from scholarship_intelligence.api.schemas import FORBIDDEN_PRIVACY_FIELDS
from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult


class CounselorContextBuilder:
    """Constructs grounded context for AI counselor from deterministic evaluation results."""

    @staticmethod
    def sanitize_student_profile(student_profile: Any) -> Dict[str, Any]:
        """Filters student profile to allowed academic/demographic fields, rejecting sensitive PII."""
        if not student_profile:
            return {}

        raw: Dict[str, Any] = {}
        if isinstance(student_profile, dict):
            raw = student_profile
        elif hasattr(student_profile, "__dict__"):
            raw = {
                k: v for k, v in student_profile.__dict__.items()
                if not k.startswith("_")
            }

        # Check and reject forbidden fields defensively
        for k in raw.keys():
            k_clean = k.lower().replace("-", "_").strip()
            if any(forbidden in k_clean for forbidden in FORBIDDEN_PRIVACY_FIELDS):
                continue

        allowed_keys = {
            "citizenship_country",
            "country_of_residence",
            "residence_country",
            "gpa",
            "gpa_scale",
            "current_education_level",
            "degree_level",
            "target_degree_level",
            "intended_major",
            "field_of_study",
            "sat_total",
            "has_sat",
            "act_composite",
            "has_act",
            "toefl_total",
            "ielts_overall",
            "financial_need_tier",
            "demonstrates_financial_need",
            "requires_visa",
            "first_generation_college_student",
            "is_first_generation",
            "prepared_components",
            "has_leadership_experience",
            "has_community_service",
            "target_academic_cycle",
        }

        sanitized: Dict[str, Any] = {}
        for k in sorted(allowed_keys):
            val = raw.get(k)
            if val is not None:
                sanitized[k] = val

        return sanitized

    @classmethod
    def build(
        cls,
        opportunity: Any,
        student_profile: Any,
        eligibility_result: EligibilityEvaluationResult,
        counselor_assessment: CounselorAssessmentResult,
        freshness_level: str = "UNVERIFIED",
    ) -> CounselorContext:
        """Assembles a complete, immutable CounselorContext."""
        opp_id = str(getattr(opportunity, "id", "unknown"))
        opp_title = getattr(opportunity, "title", "Scholarship Opportunity")
        provider = getattr(opportunity, "provider", None)
        provider_name = getattr(provider, "name", None) if provider else getattr(opportunity, "provider_name", None)
        univ = getattr(opportunity, "university", None)
        univ_name = getattr(univ, "name", None) if univ else getattr(opportunity, "university_name", None)

        # Funding decomposition
        funding_cls = "UNKNOWN"
        funding_sum = ""
        tuition_cov = "UNKNOWN"
        living_cov = "UNKNOWN"
        fees_cov = "UNKNOWN"

        funding_assessment = getattr(counselor_assessment, "funding_assessment", None) or getattr(counselor_assessment, "funding", None)
        if funding_assessment:
            funding_cls = str(funding_assessment.funding_classification.value if hasattr(funding_assessment.funding_classification, "value") else funding_assessment.funding_classification)
            tuition_cov = str(funding_assessment.tuition_covered.value if hasattr(funding_assessment.tuition_covered, "value") else funding_assessment.tuition_covered)
            living_cov = str(funding_assessment.living_expenses_covered.value if hasattr(funding_assessment.living_expenses_covered, "value") else funding_assessment.living_expenses_covered)
            fees_cov = str(funding_assessment.fees_covered.value if hasattr(funding_assessment.fees_covered, "value") else funding_assessment.fees_covered)
            funding_sum = getattr(funding_assessment, "summary", "") or getattr(counselor_assessment, "funding_understanding", "")
        elif hasattr(opportunity, "award") and opportunity.award:
            raw_fc = opportunity.award.funding_classification
            funding_cls = str(raw_fc.value if hasattr(raw_fc, "value") else raw_fc)
            funding_sum = getattr(counselor_assessment, "funding_understanding", "")

        # Deadlines list
        deadlines_list: List[Dict[str, Any]] = []
        earliest_dl = None
        dl_status = "UNKNOWN"

        if hasattr(opportunity, "deadlines") and opportunity.deadlines:
            for d in opportunity.deadlines:
                dl_date = d.deadline_date.isoformat() if hasattr(d.deadline_date, "isoformat") else str(d.deadline_date) if d.deadline_date else None
                deadlines_list.append({
                    "deadline_date": dl_date,
                    "deadline_type": str(getattr(d, "deadline_type", "UNKNOWN")),
                    "is_exact_date": bool(getattr(d, "is_exact_date", True)),
                    "academic_cycle": getattr(d, "academic_cycle", "2026-2027"),
                })

        dl_assessment = getattr(counselor_assessment, "deadline_assessment", None) or getattr(counselor_assessment, "deadlines", None)
        if dl_assessment:
            dl_status = getattr(dl_assessment, "summary", "UNKNOWN")
            earliest_obj = getattr(dl_assessment, "earliest_upcoming_deadline", None) or getattr(dl_assessment, "earliest_deadline", None)
            if earliest_obj:
                e_date = getattr(earliest_obj, "deadline_date", earliest_obj)
                earliest_dl = e_date.isoformat() if hasattr(e_date, "isoformat") else str(e_date)

        # Sources & Citations
        citations: List[SourceCitation] = []
        seen_urls = set()

        if hasattr(opportunity, "official_sources") and opportunity.official_sources:
            for s in opportunity.official_sources:
                url = getattr(s, "url", None)
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    auth_tier = getattr(s, "authority_tier", None)
                    auth_str = str(auth_tier.value if hasattr(auth_tier, "value") else auth_tier) if auth_tier else "UNKNOWN"
                    citations.append(
                        SourceCitation(
                            title=getattr(s, "page_title", None) or getattr(s, "source_domain", "Official Source"),
                            url=url,
                            authority_tier=auth_str,
                            verification_status=str(getattr(opportunity, "verification_status", "UNVERIFIED")),
                            evidence_quote=getattr(s, "extracted_text_snippet", None),
                            is_primary=bool(getattr(s, "is_primary", False)),
                        )
                    )

        if hasattr(counselor_assessment, "evidence_references") and counselor_assessment.evidence_references:
            for ref in counselor_assessment.evidence_references:
                url = ref.source_url
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    auth_tier = ref.source_authority
                    auth_str = str(auth_tier.value if hasattr(auth_tier, "value") else auth_tier) if auth_tier else "UNKNOWN"
                    citations.append(
                        SourceCitation(
                            title=ref.topic or "Evidence Source",
                            url=url,
                            authority_tier=auth_str,
                            verification_status="VERIFIED",
                            evidence_quote=ref.evidence_quote,
                            is_primary=False,
                        )
                    )

        # Build satisfied, failed, unknown rule descriptions
        satisfied = [r.explanation for r in getattr(eligibility_result, "satisfied_rules", [])]
        failed = [r.explanation for r in getattr(eligibility_result, "failed_rules", [])]
        unknown = [r.explanation for r in getattr(eligibility_result, "unknown_rules", [])]

        raw_v_status = getattr(opportunity, "verification_status", "UNVERIFIED")
        v_status_str = str(raw_v_status.value if hasattr(raw_v_status, "value") else raw_v_status)

        acad_align = counselor_assessment.academic_alignment
        acad_str = str(acad_align.level.value if hasattr(acad_align, "level") and hasattr(acad_align.level, "value") else getattr(acad_align, "level", "UNKNOWN"))

        geo_align = counselor_assessment.geographic_alignment
        geo_str = str(geo_align.level.value if hasattr(geo_align, "level") and hasattr(geo_align.level, "value") else getattr(geo_align, "level", "UNKNOWN"))

        prog_align = counselor_assessment.program_alignment
        prog_str = str(prog_align.level.value if hasattr(prog_align, "level") and hasattr(prog_align.level, "value") else getattr(prog_align, "level", "UNKNOWN"))

        test_read = counselor_assessment.testing_readiness
        test_str = str(test_read.level.value if hasattr(test_read, "level") and hasattr(test_read.level, "value") else getattr(test_read, "level", "UNKNOWN"))

        app_read = counselor_assessment.application_readiness
        app_str = str(app_read.level.value if hasattr(app_read, "level") and hasattr(app_read.level, "value") else getattr(app_read, "level", "UNKNOWN"))

        warnings_list: List[str] = []
        if hasattr(counselor_assessment, "warnings") and counselor_assessment.warnings:
            for w in counselor_assessment.warnings:
                warnings_list.append(w.message if hasattr(w, "message") else str(w))

        # Compute epistemic grounding status deterministically
        assessment_unknowns = getattr(counselor_assessment, "unknowns", None) or getattr(counselor_assessment, "uncertainties", []) or []
        if v_status_str == "CONFLICTING" or any("conflict" in str(u).lower() for u in assessment_unknowns):
            epistemic_st = EpistemicStatus.CONFLICTING_INFORMATION
        elif v_status_str == "UNVERIFIED" or (str(getattr(eligibility_result, "status", "")) == "NEEDS_INFORMATION" and len(unknown) > 0):
            epistemic_st = EpistemicStatus.INSUFFICIENT_INFORMATION
        elif v_status_str == "PARTIALLY_VERIFIED" or len(unknown) > 0 or len(warnings_list) > 0:
            epistemic_st = EpistemicStatus.PARTIALLY_GROUNDED
        else:
            epistemic_st = EpistemicStatus.GROUNDED

        return CounselorContext(
            opportunity_id=opp_id,
            opportunity_title=opp_title,
            provider_name=provider_name,
            university_name=univ_name,
            target_degree_level=getattr(opportunity, "target_degree_level", "BACHELOR"),
            destination_country=getattr(opportunity, "destination_country", "US"),
            academic_cycle=getattr(opportunity, "academic_cycle", "2026-2027"),
            verification_status=v_status_str,
            freshness_level=freshness_level,
            epistemic_status=epistemic_st,
            funding_classification=funding_cls,
            funding_summary=funding_sum,
            tuition_covered=tuition_cov,
            living_expenses_covered=living_cov,
            fees_covered=fees_cov,
            deadlines=deadlines_list,
            earliest_deadline=earliest_dl,
            deadline_status=dl_status,
            eligibility_status=str(eligibility_result.status.value if hasattr(eligibility_result.status, "value") else eligibility_result.status),
            academic_alignment=acad_str,
            geographic_alignment=geo_str,
            program_alignment=prog_str,
            testing_readiness=test_str,
            application_readiness=app_str,
            student_profile_facts=cls.sanitize_student_profile(student_profile),
            satisfied_rules=sorted(satisfied),
            failed_rules=sorted(failed),
            unknown_rules=sorted(unknown),
            strengths=sorted(getattr(counselor_assessment, "strengths", []) or []),
            gaps=sorted(getattr(counselor_assessment, "gaps", []) or []),
            uncertainties=sorted(getattr(counselor_assessment, "unknowns", None) or getattr(counselor_assessment, "uncertainties", []) or []),
            warnings=warnings_list,
            next_steps=sorted(getattr(counselor_assessment, "recommended_next_steps", None) or getattr(counselor_assessment, "recommended_actions", []) or []),
            evidence_sources=citations,
        )
