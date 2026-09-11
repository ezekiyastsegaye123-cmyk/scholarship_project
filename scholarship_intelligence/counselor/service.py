"""Scholarship Counselor Service.

Coordinates:
- Student Profile facts
- Scholarship Opportunity details
- Phase 1D EligibilityEvaluationResult
- Source Verification & Provenance

Produces:
- Structured, explainable, qualitative counselor decision-support output.
- Zero numerical scores, zero acceptance probabilities, zero ranking.
"""
from datetime import date, datetime, timezone
from typing import Any, List, Optional

from scholarship_intelligence.counselor.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)
from scholarship_intelligence.counselor.rules import (
    assess_academic_alignment,
    assess_application_readiness,
    assess_deadlines,
    assess_funding,
    assess_geographic_alignment,
    assess_program_alignment,
    assess_testing_readiness,
)
from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    FundingClassification,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.counselor import (
    CounselorAssessmentResult,
    DeadlineAssessmentContext,
    EvidenceReference,
    VerificationWarningContext,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
)


class ScholarshipCounselorService:
    """Qualitative decision-support counselor service for scholarship opportunities."""

    def assess_opportunity(
        self,
        student_profile: Any,
        opportunity: Any,
        eligibility_result: EligibilityEvaluationResult,
        reference_date: Optional[date] = None,
        evaluated_at: Optional[datetime] = None,
    ) -> CounselorAssessmentResult:
        """Generates a complete qualitative counselor assessment.

        Deterministic evaluation contract:
        - If evaluated_at is provided, it is used verbatim as the evaluation timestamp.
        - If evaluated_at is None and reference_date is provided, evaluated_at deterministically
          defaults to midnight UTC on reference_date (ensuring identical input -> bitwise identical JSON).
        - If both are None (only permissible when opportunity has no deadlines), evaluated_at
          falls back to current UTC time.
        """
        opp_id = getattr(opportunity, "id", None)
        opp_title = getattr(opportunity, "title", None) or "Scholarship Opportunity"
        student_id = getattr(student_profile, "id", None) if not isinstance(student_profile, dict) else student_profile.get("id")

        # Resolve evaluation timestamp deterministically
        if evaluated_at is not None:
            eval_time = evaluated_at
        elif reference_date is not None:
            eval_time = datetime.combine(reference_date, datetime.min.time(), tzinfo=timezone.utc)
        else:
            eval_time = datetime.now(timezone.utc)

        # 1. Dimensional qualitative evaluations
        academic_ctx = assess_academic_alignment(student_profile, opportunity, eligibility_result)
        geo_ctx = assess_geographic_alignment(student_profile, opportunity, eligibility_result)
        prog_ctx = assess_program_alignment(student_profile, opportunity, eligibility_result)
        test_ctx = assess_testing_readiness(student_profile, opportunity, eligibility_result)
        funding_ctx = assess_funding(opportunity)
        app_ctx = assess_application_readiness(student_profile, opportunity)
        opp_deadlines = getattr(opportunity, "deadlines", []) or []
        if reference_date is not None:
            deadline_ctx = assess_deadlines(opportunity, reference_date=reference_date)
        elif not opp_deadlines:
            deadline_ctx = DeadlineAssessmentContext(
                deadlines=[],
                has_passed_deadline=False,
                earliest_upcoming_deadline=None,
                summary="No deadlines currently published for this opportunity.",
            )
        else:
            raise ValueError(
                "reference_date is required for deterministic deadline assessment when opportunity publishes deadlines; "
                "machine-clock fallback is prohibited"
            )

        # 2. Verification context
        v_status_raw = getattr(opportunity, "verification_status", VerificationState.UNVERIFIED.value)
        v_status = VerificationState(v_status_raw) if isinstance(v_status_raw, str) else v_status_raw
        contains_unverified = bool(
            eligibility_result.evaluation_contains_unverified_facts
            or v_status == VerificationState.PARTIALLY_VERIFIED
        )

        verif_warning = False
        verif_msg = None
        if contains_unverified or v_status == VerificationState.PARTIALLY_VERIFIED:
            verif_warning = True
            verif_msg = (
                "Notice: Some opportunity requirements are only PARTIALLY_VERIFIED. "
                "Confirm guidelines directly on the official provider portal before submitting."
            )
        elif v_status == VerificationState.CONFLICTING:
            verif_warning = True
            verif_msg = "Notice: Contradictory evidence exists across official sources. Manual review required."
        elif v_status == VerificationState.UNVERIFIED:
            verif_warning = True
            verif_msg = "Notice: Opportunity information is UNVERIFIED. Direct provider verification required."
        elif v_status == VerificationState.OUTDATED:
            verif_warning = True
            verif_msg = "Notice: Opportunity verification is OUTDATED. Rules must be reverified for current cycle."
        elif v_status == VerificationState.SOURCE_UNAVAILABLE:
            verif_warning = True
            verif_msg = "Notice: Official provider source is currently UNAVAILABLE or inaccessible."
        elif v_status == VerificationState.QUARANTINED_FOR_REVIEW:
            verif_warning = True
            verif_msg = "Notice: Opportunity is QUARANTINED_FOR_REVIEW due to material verification concerns."

        verif_ctx = VerificationWarningContext(
            verification_status=v_status,
            evaluation_contains_unverified_facts=contains_unverified,
            has_warning=verif_warning,
            warning_message=verif_msg,
        )

        # 3. Synthesize strengths
        strengths: List[str] = []
        if eligibility_result.status == EligibilityStatus.ELIGIBLE:
            strengths.append("Meets all published mandatory eligibility conditions.")
        if academic_ctx.level == AlignmentLevel.STRONG:
            strengths.append("Academic GPA record satisfies published eligibility criteria.")
        if geo_ctx.level == AlignmentLevel.STRONG:
            strengths.append("Citizenship and residency align with eligible international applicant criteria.")
        if prog_ctx.level == AlignmentLevel.STRONG:
            strengths.append(f"Declared major aligns with targeted fields of study ({prog_ctx.eligible_programs}).")
        if test_ctx.level == ReadinessLevel.READY:
            strengths.append("Standardized test requirements are confirmed satisfied.")
        if funding_ctx.funding_classification == FundingClassification.FULL_FUNDING:
            strengths.append("Comprehensive full funding covers tuition and living expenses.")
        elif funding_ctx.funding_classification == FundingClassification.FULL_TUITION:
            strengths.append("High financial value: 100% full tuition coverage verified.")

        # 4. Synthesize gaps
        gaps: List[str] = []
        if eligibility_result.status == EligibilityStatus.INELIGIBLE:
            for r in eligibility_result.failed_rules:
                gaps.append(f"Unmet mandatory rule: {r.explanation}")
        if academic_ctx.level == AlignmentLevel.LIMITED:
            gaps.append("Academic GPA falls below the published minimum criterion.")
        if geo_ctx.level == AlignmentLevel.LIMITED:
            gaps.append("Citizenship or residence is outside eligible geographic categories.")
        if prog_ctx.level == AlignmentLevel.LIMITED:
            gaps.append("Declared major is not among published eligible study programs.")
        if test_ctx.level == ReadinessLevel.NEEDS_PREPARATION:
            gaps.append("Required standardized tests (SAT/ACT) are not on record or do not satisfy published requirements.")
        if deadline_ctx.has_passed_deadline:
            gaps.append("One or more published application deadlines have passed for the current cycle.")

        # 5. Synthesize unknowns
        unknowns: List[str] = []
        if eligibility_result.status == EligibilityStatus.NEEDS_INFORMATION:
            for r in eligibility_result.unknown_rules:
                unknowns.append(f"Information needed: {r.explanation}")
        if academic_ctx.level == AlignmentLevel.UNKNOWN:
            unknowns.append("Student GPA or grade scale has not been provided.")
        if geo_ctx.level == AlignmentLevel.UNKNOWN:
            unknowns.append("Geographic eligibility criteria or student citizenship is unconfirmed.")
        if prog_ctx.level == AlignmentLevel.UNKNOWN:
            if prog_ctx.has_major_restriction:
                unknowns.append("Declared major is needed to confirm program eligibility.")
            else:
                unknowns.append("Eligible fields of study were not specified; confirm program restrictions with provider.")
        if test_ctx.level == ReadinessLevel.UNKNOWN:
            unknowns.append("Provider standardized testing requirements are unconfirmed or under review.")
        if app_ctx.level == ReadinessLevel.UNKNOWN:
            unknowns.append("Student document preparation status for required application materials is unrecorded.")
        if funding_ctx.living_expenses_covered == TriState.UNKNOWN and funding_ctx.funding_classification != FundingClassification.FULL_FUNDING:
            unknowns.append("Coverage of room, board, and personal living expenses is unverified.")

        # 6. Synthesize warnings
        warnings: List[str] = []
        if eligibility_result.status == EligibilityStatus.INELIGIBLE:
            warnings.append("Application is not advised: One or more mandatory eligibility requirements are not met.")
        elif eligibility_result.status == EligibilityStatus.NEEDS_INFORMATION:
            warnings.append("Eligibility cannot be established until missing profile facts are supplied.")
        elif eligibility_result.status == EligibilityStatus.NEEDS_REVIEW:
            warnings.append("Unresolved conflicting data or quarantine status requires counselor review.")

        if verif_ctx.has_warning and verif_ctx.warning_message:
            warnings.append(verif_ctx.warning_message)

        if funding_ctx.funding_classification == FundingClassification.FULL_TUITION:
            warnings.append(
                "Funding Notice: Full tuition coverage does not include room, meals, or living stipends. "
                "Student must budget for non-tuition costs."
            )

        if deadline_ctx.earliest_upcoming_deadline and deadline_ctx.earliest_upcoming_deadline.readiness == DeadlineReadiness.CLOSING_SOON:
            warnings.append(
                f"Approaching deadline: {deadline_ctx.earliest_upcoming_deadline.deadline_type.value} "
                f"closes on {deadline_ctx.earliest_upcoming_deadline.deadline_date} "
                f"({deadline_ctx.earliest_upcoming_deadline.days_remaining} days remaining)."
            )

        # 7. Actionable next steps
        recommended_next_steps: List[str] = []
        if eligibility_result.status == EligibilityStatus.INELIGIBLE:
            recommended_next_steps.append("Explore alternative opportunities with criteria matching your academic profile.")
        elif eligibility_result.status == EligibilityStatus.NEEDS_INFORMATION:
            recommended_next_steps.append("Complete your profile by providing your GPA, intended major, and citizenship.")

        if deadline_ctx.earliest_upcoming_deadline:
            recommended_next_steps.append(
                f"Confirm the {deadline_ctx.earliest_upcoming_deadline.deadline_type.value} deadline "
                f"({deadline_ctx.earliest_upcoming_deadline.deadline_date}) directly with the provider."
            )

        if test_ctx.level == ReadinessLevel.NEEDS_PREPARATION:
            recommended_next_steps.append("Register for and complete required standardized exams (SAT or ACT).")

        if app_ctx.required_components:
            recommended_next_steps.append(
                f"Prepare required application materials: {', '.join(app_ctx.required_components)}."
            )

        if funding_ctx.funding_classification == FundingClassification.FULL_TUITION:
            recommended_next_steps.append(
                "Review the university's Cost of Attendance to determine housing and dining expenses."
            )

        if verif_ctx.has_warning:
            recommended_next_steps.append(
                "Verify award guidelines with the official scholarship provider before submitting your application."
            )

        # 8. Collect evidence references
        evidence_references: List[EvidenceReference] = []
        # From official sources
        official_sources = getattr(opportunity, "official_sources", []) or []
        for src in official_sources:
            raw_url = getattr(src, "url", None) or getattr(src, "source_url", None)
            url = str(raw_url) if isinstance(raw_url, str) else None
            auth = getattr(src, "authority_tier", AuthorityTier.OFFICIAL_PROVIDER)
            if isinstance(auth, str):
                try:
                    auth = AuthorityTier(auth)
                except ValueError:
                    auth = AuthorityTier.OFFICIAL_PROVIDER

            # Extract genuine text snippet if present; never invent placeholder text
            raw_snippet = getattr(src, "extracted_text_snippet", None) or getattr(src, "source_evidence_snippet", None)
            snippet = str(raw_snippet) if isinstance(raw_snippet, str) else None

            evidence_references.append(
                EvidenceReference(
                    topic="Official Source Portal",
                    source_url=url,
                    source_authority=auth,
                    evidence_quote=snippet,
                )
            )

        # From academic / rules evidence
        for snippet in academic_ctx.evidence_snippets:
            evidence_references.append(
                EvidenceReference(
                    topic="Academic Requirement",
                    evidence_quote=snippet,
                )
            )

        # From geographic evidence
        for snippet in geo_ctx.evidence_snippets:
            evidence_references.append(
                EvidenceReference(
                    topic="Geographic Eligibility",
                    evidence_quote=snippet,
                )
            )

        # From program evidence
        for snippet in prog_ctx.evidence_snippets:
            evidence_references.append(
                EvidenceReference(
                    topic="Program of Study",
                    evidence_quote=snippet,
                )
            )

        # From testing evidence
        for snippet in test_ctx.evidence_snippets:
            evidence_references.append(
                EvidenceReference(
                    topic="Standardized Testing",
                    evidence_quote=snippet,
                )
            )

        # From funding evidence
        for snippet in funding_ctx.evidence_snippets:
            evidence_references.append(
                EvidenceReference(
                    topic="Funding & Award Terms",
                    evidence_quote=snippet,
                )
            )

        # From deadline evidence
        for d in deadline_ctx.deadlines:
            if d.evidence_snippet:
                evidence_references.append(
                    EvidenceReference(
                        topic=f"Deadline ({d.deadline_type.value})",
                        evidence_quote=d.evidence_snippet,
                    )
                )

        # Eligibility summary text
        elig_summary = f"Status: {eligibility_result.status.value}."
        if eligibility_result.explanations:
            elig_summary += f" {eligibility_result.explanations[0]}"

        return CounselorAssessmentResult(
            opportunity_id=opp_id,
            opportunity_title=opp_title,
            student_id=student_id,
            eligibility_status=eligibility_result.status,
            eligibility_summary=elig_summary,
            academic_alignment=academic_ctx,
            geographic_alignment=geo_ctx,
            program_alignment=prog_ctx,
            testing_readiness=test_ctx,
            funding_assessment=funding_ctx,
            application_readiness=app_ctx,
            deadline_assessment=deadline_ctx,
            verification_context=verif_ctx,
            strengths=strengths,
            gaps=gaps,
            unknowns=unknowns,
            warnings=warnings,
            recommended_next_steps=recommended_next_steps,
            evidence_references=evidence_references,
            evaluated_at=eval_time,
        )
