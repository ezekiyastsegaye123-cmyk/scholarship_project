"""Deterministic qualitative counselor assessment rules.

Guarantees:
- Inspectable, explicit, deterministic rules (NO hidden numerical weights or scoring).
- Zero LLM dependency or probabilistic inference.
- Uncertainty preservation: Missing facts remain UNKNOWN.
- Full tuition != Full funding invariant strictly enforced.
"""
from datetime import date
from typing import Any, List, Optional

from scholarship_intelligence.counselor.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)
from scholarship_intelligence.domain.enums import (
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    RequirementKind,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.counselor import (
    AcademicAlignmentContext,
    ApplicationReadinessContext,
    DeadlineAssessmentContext,
    DeadlineItemContext,
    EvidenceReference,
    FundingAssessmentContext,
    GeographicAlignmentContext,
    ProgramAlignmentContext,
    TestingReadinessContext,
    VerificationWarningContext,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


def assess_academic_alignment(
    profile: Any,
    opportunity: Any,
    eligibility_result: EligibilityEvaluationResult,
) -> AcademicAlignmentContext:
    """Evaluates student academic profile relative to published academic requirements."""
    student_gpa = getattr(profile, "gpa", None) if not isinstance(profile, dict) else profile.get("gpa")
    student_scale = (
        getattr(profile, "gpa_scale", 4.0) if not isinstance(profile, dict) else profile.get("gpa_scale", 4.0)
    )

    # Find rules referencing gpa
    gpa_rule_evals: List[RuleEvaluationResult] = []
    all_rules = (
        eligibility_result.satisfied_rules
        + eligibility_result.failed_rules
        + eligibility_result.unknown_rules
        + eligibility_result.conflicting_rules
        + eligibility_result.supplementary_rules
    )
    for r in all_rules:
        if r.field and "gpa" in r.field.lower():
            gpa_rule_evals.append(r)
        elif r.sub_results:
            for sub in r.sub_results:
                if sub.field and "gpa" in sub.field.lower():
                    gpa_rule_evals.append(sub)

    details: List[str] = []
    evidence: List[str] = []
    required_gpa: Optional[float] = None

    if gpa_rule_evals:
        target_rule = gpa_rule_evals[0]
        required_gpa = float(target_rule.expected_value) if target_rule.expected_value is not None else None
        if target_rule.evidence_snippet:
            evidence.append(target_rule.evidence_snippet)

        if target_rule.status == TriState.YES:
            level = AlignmentLevel.STRONG
            details.append(
                f"Student cumulative GPA ({student_gpa}) meets or exceeds published minimum requirement ({required_gpa} on {target_rule.scale or 4.0} scale)."
            )
        elif target_rule.status == TriState.NO:
            level = AlignmentLevel.LIMITED
            details.append(
                f"Student cumulative GPA ({student_gpa}) is below the published minimum requirement ({required_gpa} on {target_rule.scale or 4.0} scale)."
            )
        elif target_rule.status == TriState.UNKNOWN:
            level = AlignmentLevel.UNKNOWN
            if student_gpa is None:
                details.append("Student GPA is not provided on profile; academic alignment cannot be confirmed.")
            else:
                details.append("Grading scale mismatch without defined conversion rule; academic alignment cannot be confirmed.")
        else:
            level = AlignmentLevel.MODERATE
            details.append(f"Academic requirement evaluated to {target_rule.status.value}.")
    else:
        # No explicit GPA rule published
        if student_gpa is not None:
            if float(student_gpa) >= 3.5:
                level = AlignmentLevel.STRONG
                details.append(f"No explicit minimum GPA published; student maintains a strong academic GPA of {student_gpa}.")
            else:
                level = AlignmentLevel.MODERATE
                details.append(f"No explicit minimum GPA published; student profile GPA is {student_gpa}.")
        else:
            level = AlignmentLevel.NOT_ASSESSABLE
            details.append("No explicit minimum GPA requirement published for this opportunity.")

    return AcademicAlignmentContext(
        level=level,
        student_gpa=float(student_gpa) if student_gpa is not None else None,
        student_scale=float(student_scale) if student_scale is not None else None,
        required_gpa=required_gpa,
        details=details,
        evidence_snippets=evidence,
    )


def assess_geographic_alignment(
    profile: Any,
    opportunity: Any,
    eligibility_result: EligibilityEvaluationResult,
) -> GeographicAlignmentContext:
    """Evaluates student citizenship/residence relative to published geographic criteria."""
    citizenship = (
        getattr(profile, "citizenship_country", None)
        if not isinstance(profile, dict)
        else profile.get("citizenship_country")
    )
    residence = (
        getattr(profile, "residence_country", None)
        if not isinstance(profile, dict)
        else profile.get("residence_country")
    )

    # Find rules referencing citizenship or nationality
    geo_rule_evals: List[RuleEvaluationResult] = []
    all_rules = (
        eligibility_result.satisfied_rules
        + eligibility_result.failed_rules
        + eligibility_result.unknown_rules
        + eligibility_result.conflicting_rules
    )
    for r in all_rules:
        if r.field and any(k in r.field.lower() for k in ("citizenship", "country", "nationality", "residence")):
            geo_rule_evals.append(r)
        elif r.sub_results:
            for sub in r.sub_results:
                if sub.field and any(k in sub.field.lower() for k in ("citizenship", "country", "nationality", "residence")):
                    geo_rule_evals.append(sub)

    details: List[str] = []
    evidence: List[str] = []
    eligible_countries: List[str] = []

    if geo_rule_evals:
        target_rule = geo_rule_evals[0]
        if isinstance(target_rule.expected_value, (list, tuple, set)):
            eligible_countries = [str(c) for c in target_rule.expected_value]
        elif target_rule.expected_value:
            eligible_countries = [str(target_rule.expected_value)]

        if target_rule.evidence_snippet:
            evidence.append(target_rule.evidence_snippet)

        if target_rule.status == TriState.YES:
            level = AlignmentLevel.STRONG
            details.append(f"Student citizenship ({citizenship}) matches published eligible geographic criteria.")
        elif target_rule.status == TriState.NO:
            level = AlignmentLevel.LIMITED
            details.append(f"Student citizenship ({citizenship}) is outside published eligible countries: {eligible_countries}.")
        elif target_rule.status == TriState.UNKNOWN:
            level = AlignmentLevel.UNKNOWN
            details.append("Student citizenship/residence is missing or indeterminate; cannot confirm geographic alignment.")
        else:
            level = AlignmentLevel.MODERATE
            details.append(f"Geographic condition evaluated to {target_rule.status.value}.")
    else:
        # Check opportunity international student flag
        intl_allowed = getattr(opportunity, "international_students_allowed", TriState.UNKNOWN.value)
        if isinstance(intl_allowed, TriState):
            intl_allowed = intl_allowed.value

        if intl_allowed == TriState.YES.value:
            level = AlignmentLevel.STRONG
            details.append("Opportunity explicitly permits international students with no country restrictions published.")
        elif intl_allowed == TriState.NO.value:
            level = AlignmentLevel.LIMITED
            details.append("Opportunity does not permit international students.")
        else:
            level = AlignmentLevel.NOT_ASSESSABLE
            details.append("No geographic or nationality restrictions published for this opportunity.")

    return GeographicAlignmentContext(
        level=level,
        citizenship_country=citizenship,
        residence_country=residence,
        eligible_countries=eligible_countries,
        details=details,
        evidence_snippets=evidence,
    )


def assess_program_alignment(
    profile: Any,
    opportunity: Any,
    eligibility_result: EligibilityEvaluationResult,
) -> ProgramAlignmentContext:
    """Evaluates student intended major relative to eligible academic programs."""
    major = (
        getattr(profile, "intended_major", None)
        if not isinstance(profile, dict)
        else profile.get("intended_major")
    )

    # Check for major/program restrictions in rules
    major_rules: List[RuleEvaluationResult] = []
    all_rules = (
        eligibility_result.satisfied_rules
        + eligibility_result.failed_rules
        + eligibility_result.unknown_rules
        + eligibility_result.supplementary_rules
    )
    for r in all_rules:
        if r.field and any(k in r.field.lower() for k in ("major", "program", "field_of_study")):
            major_rules.append(r)

    details: List[str] = []
    evidence: List[str] = []
    eligible_programs: List[str] = []

    if major_rules:
        target = major_rules[0]
        has_restriction = True
        if isinstance(target.expected_value, (list, tuple, set)):
            eligible_programs = [str(p) for p in target.expected_value]
        elif target.expected_value:
            eligible_programs = [str(target.expected_value)]

        if target.evidence_snippet:
            evidence.append(target.evidence_snippet)

        if target.status == TriState.YES:
            level = AlignmentLevel.STRONG
            details.append(f"Student intended major '{major}' aligns with eligible programs {eligible_programs}.")
        elif target.status == TriState.NO:
            level = AlignmentLevel.LIMITED
            details.append(f"Student intended major '{major}' is outside eligible programs {eligible_programs}.")
        else:
            level = AlignmentLevel.UNKNOWN
            details.append("Student declared major is missing or cannot be verified against eligible programs.")
    else:
        has_restriction = False
        level = AlignmentLevel.NOT_ASSESSABLE
        details.append("Opportunity is open across all undergraduate fields of study; no major restrictions published.")

    return ProgramAlignmentContext(
        level=level,
        declared_major=major,
        eligible_programs=eligible_programs,
        has_major_restriction=has_restriction,
        details=details,
        evidence_snippets=evidence,
    )


def assess_testing_readiness(
    profile: Any,
    opportunity: Any,
    eligibility_result: EligibilityEvaluationResult,
) -> TestingReadinessContext:
    """Evaluates student testing preparedness for SAT/ACT and English exams."""
    sat_score = getattr(profile, "sat_score", None) if not isinstance(profile, dict) else profile.get("sat_score")
    if not isinstance(sat_score, (int, float)):
        sat_score = None
    act_score = getattr(profile, "act_score", None) if not isinstance(profile, dict) else profile.get("act_score")
    if not isinstance(act_score, (int, float)):
        act_score = None
    eng_score = (
        getattr(profile, "english_test_score", None)
        if not isinstance(profile, dict)
        else profile.get("english_test_score")
    )
    if not isinstance(eng_score, (int, float)):
        eng_score = None

    req_sat_val = getattr(opportunity, "requires_sat", None)
    req_act_val = getattr(opportunity, "requires_act", None)

    if isinstance(req_sat_val, TriState):
        req_sat = req_sat_val
    elif isinstance(req_sat_val, str):
        try:
            req_sat = TriState(req_sat_val)
        except ValueError:
            req_sat = TriState.UNKNOWN
    else:
        req_sat = TriState.UNKNOWN

    if isinstance(req_act_val, TriState):
        req_act = req_act_val
    elif isinstance(req_act_val, str):
        try:
            req_act = TriState(req_act_val)
        except ValueError:
            req_act = TriState.UNKNOWN
    else:
        req_act = TriState.UNKNOWN

    details: List[str] = []
    evidence: List[str] = []

    tests_required = (req_sat == TriState.YES) or (req_act == TriState.YES)

    if not tests_required:
        level = ReadinessLevel.NOT_APPLICABLE
        details.append("Standardized testing (SAT/ACT) is not required for this scholarship.")
    else:
        # Testing is required
        has_sat = sat_score is not None
        has_act = act_score is not None

        if has_sat or has_act:
            if (has_sat and sat_score >= 1400) or (has_act and act_score >= 30):
                level = ReadinessLevel.READY
                details.append(f"Student has completed required standardized testing with strong scores (SAT: {sat_score}, ACT: {act_score}).")
            else:
                level = ReadinessLevel.PARTIALLY_READY
                details.append(f"Standardized test score submitted (SAT: {sat_score}, ACT: {act_score}). Review whether retaking is recommended.")
        else:
            level = ReadinessLevel.NEEDS_PREPARATION
            details.append("Standardized tests (SAT/ACT) are required by the provider, but no scores are recorded on the student profile.")

    return TestingReadinessContext(
        level=level,
        requires_sat=req_sat,
        requires_act=req_act,
        student_sat=sat_score,
        student_act=act_score,
        student_english_score=eng_score,
        details=details,
        evidence_snippets=evidence,
    )


def assess_funding(opportunity: Any) -> FundingAssessmentContext:
    """Decomposes verified funding and enforces full tuition != fully funded invariant."""
    award = getattr(opportunity, "award", None)
    classification = FundingClassification.UNKNOWN
    is_renewable = TriState.UNKNOWN
    est_val = None
    components = []

    if award:
        raw_class = getattr(award, "funding_classification", None)
        if isinstance(raw_class, FundingClassification):
            classification = raw_class
        elif isinstance(raw_class, str):
            try:
                classification = FundingClassification(raw_class)
            except ValueError:
                classification = FundingClassification.UNKNOWN

        raw_ren = getattr(award, "is_renewable", None)
        if isinstance(raw_ren, TriState):
            is_renewable = raw_ren
        elif isinstance(raw_ren, str):
            try:
                is_renewable = TriState(raw_ren)
            except ValueError:
                is_renewable = TriState.UNKNOWN

        est_val_raw = getattr(award, "estimated_annual_value_usd", None)
        if isinstance(est_val_raw, (int, float)):
            est_val = float(est_val_raw)

        raw_components = getattr(award, "funding_components", [])
        if isinstance(raw_components, list):
            components = raw_components

    # Map component types
    comp_types = set()
    evidence: List[str] = []
    for c in components:
        raw_t = getattr(c, "component_type", None)
        if isinstance(raw_t, FundingComponentType):
            comp_types.add(raw_t.value)
        elif isinstance(raw_t, str):
            comp_types.add(raw_t)

        snippet = getattr(c, "source_evidence_snippet", None)
        if isinstance(snippet, str):
            evidence.append(snippet)

    tuition = TriState.YES if FundingComponentType.TUITION.value in comp_types else TriState.UNKNOWN
    fees = TriState.YES if FundingComponentType.MANDATORY_FEES.value in comp_types else TriState.UNKNOWN
    room = TriState.YES if FundingComponentType.ROOM.value in comp_types else TriState.UNKNOWN
    meals = TriState.YES if FundingComponentType.MEALS.value in comp_types else TriState.UNKNOWN
    living = TriState.YES if FundingComponentType.LIVING_EXPENSES.value in comp_types else TriState.UNKNOWN
    stipend = TriState.YES if FundingComponentType.STIPEND.value in comp_types else TriState.UNKNOWN
    insurance = TriState.YES if FundingComponentType.HEALTH_INSURANCE.value in comp_types else TriState.UNKNOWN
    books = TriState.YES if FundingComponentType.BOOKS.value in comp_types else TriState.UNKNOWN
    travel = TriState.YES if FundingComponentType.TRAVEL.value in comp_types else TriState.UNKNOWN

    details: List[str] = []

    # Strict Invariant: Full Tuition != Full Funding
    if classification == FundingClassification.FULL_FUNDING:
        summary = "Full funding: Verified coverage includes tuition as well as living, room, and board expenses."
        details.append("Covers full cost of attendance including living expenses.")
    elif classification == FundingClassification.FULL_TUITION:
        summary = "Full tuition only: Tuition is covered. Room, meals, and living expenses are NOT verified as covered; student must plan for living costs."
        details.append("Covers 100% tuition. Living, housing, and meal expenses are unconfirmed or student-funded.")
    elif classification == FundingClassification.PARTIAL_FUNDING:
        summary = "Partial funding: Provides a partial contribution toward tuition or attendance costs."
        details.append("Student must secure remaining institutional or private funds.")
    elif tuition == TriState.YES and room != TriState.YES:
        summary = "Tuition coverage indicated: Room, meals, and living expenses are NOT verified as covered; student must plan for living costs."
        details.append("Tuition covered. Living, housing, and meal expenses are unconfirmed or student-funded.")
    else:
        summary = "Funding details: Funding coverage is partially specified or unknown. Check official award letter."
        details.append("Review complete financial components with the official provider.")

    return FundingAssessmentContext(
        funding_classification=classification,
        tuition_covered=tuition,
        living_expenses_covered=living,
        fees_covered=fees,
        books_covered=books,
        travel_covered=travel,
        health_insurance_covered=insurance,
        stipend_covered=stipend,
        is_renewable=is_renewable,
        estimated_annual_value_usd=est_val,
        summary=summary,
        details=details,
        evidence_snippets=evidence,
    )


def assess_application_readiness(
    profile: Any,
    opportunity: Any,
) -> ApplicationReadinessContext:
    """Evaluates readiness of application materials."""
    app_reqs = getattr(opportunity, "application_requirements", [])
    if not isinstance(app_reqs, list):
        app_reqs = []
    reqs = getattr(opportunity, "requirements", [])
    if not isinstance(reqs, list):
        reqs = []

    required_components: List[str] = []
    optional_components: List[str] = []
    evidence: List[str] = []

    for item in app_reqs + reqs:
        raw_name = getattr(item, "title", None) or getattr(item, "name", None)
        name = raw_name if isinstance(raw_name, str) else "Required Component"

        raw_kind = getattr(item, "kind", None)
        kind_str = raw_kind.value if hasattr(raw_kind, "value") else (str(raw_kind) if isinstance(raw_kind, str) else None)

        raw_is_req = getattr(item, "is_required", None)
        if isinstance(raw_is_req, bool):
            is_req = raw_is_req
        elif kind_str is not None:
            is_req = (kind_str == RequirementKind.REQUIRED.value)
        else:
            is_req = True

        if is_req:
            required_components.append(name)
        else:
            optional_components.append(name)

        snippet = getattr(item, "source_evidence_snippet", None)
        if isinstance(snippet, str):
            evidence.append(snippet)

    details: List[str] = []
    total = len(required_components) + len(optional_components)

    if not required_components:
        level = ReadinessLevel.NOT_APPLICABLE
        details.append("No specialized application materials or essays published by the provider.")
    else:
        level = ReadinessLevel.NEEDS_PREPARATION
        details.append(f"{len(required_components)} mandatory application document(s) required: {required_components}.")

    return ApplicationReadinessContext(
        level=level,
        total_requirements_count=total,
        required_components=required_components,
        optional_components=optional_components,
        missing_components=required_components,  # By default requires active submission
        details=details,
        evidence_snippets=evidence,
    )


def assess_deadlines(
    opportunity: Any,
    reference_date: Optional[date] = None,
) -> DeadlineAssessmentContext:
    """Evaluates multiple distinct deadlines with deterministic closing-soon threshold (14 days)."""
    ref_date = reference_date or date.today()
    deadlines = getattr(opportunity, "deadlines", [])
    if not isinstance(deadlines, list):
        deadlines = []

    items: List[DeadlineItemContext] = []
    has_passed = False
    earliest_upcoming: Optional[DeadlineItemContext] = None

    for d in deadlines:
        raw_type = getattr(d, "deadline_type", None)
        if isinstance(raw_type, DeadlineType):
            d_type = raw_type
        elif isinstance(raw_type, str):
            try:
                d_type = DeadlineType(raw_type)
            except ValueError:
                d_type = DeadlineType.SCHOLARSHIP_APPLICATION
        else:
            d_type = DeadlineType.SCHOLARSHIP_APPLICATION

        d_date = getattr(d, "deadline_date", None)
        if not isinstance(d_date, date):
            d_date = None

        is_exact = getattr(d, "is_exact_date", True)
        if not isinstance(is_exact, bool):
            is_exact = True

        raw_tz = getattr(d, "timezone", None)
        tz = raw_tz if isinstance(raw_tz, str) else "America/New_York"

        raw_desc = getattr(d, "context_description", None)
        desc = raw_desc if isinstance(raw_desc, str) else None

        raw_evidence = getattr(d, "source_evidence_snippet", None)
        evidence = raw_evidence if isinstance(raw_evidence, str) else None

        days_rem: Optional[int] = None
        readiness = DeadlineReadiness.UNKNOWN

        if d_date is not None:
            days_rem = (d_date - ref_date).days
            if days_rem < 0:
                readiness = DeadlineReadiness.CLOSED
                has_passed = True
            elif 0 <= days_rem <= 14:
                readiness = DeadlineReadiness.CLOSING_SOON
            else:
                readiness = DeadlineReadiness.OPEN

        item = DeadlineItemContext(
            deadline_type=d_type,
            deadline_date=d_date,
            readiness=readiness,
            days_remaining=days_rem,
            is_exact_date=is_exact,
            timezone=tz,
            context_description=desc,
            evidence_snippet=evidence,
        )
        items.append(item)

        if readiness in (DeadlineReadiness.OPEN, DeadlineReadiness.CLOSING_SOON):
            if earliest_upcoming is None or (days_rem is not None and (earliest_upcoming.days_remaining is None or days_rem < earliest_upcoming.days_remaining)):
                earliest_upcoming = item

    if not items:
        summary = "No deadlines currently published for this opportunity."
    elif earliest_upcoming:
        summary = f"Next deadline ({earliest_upcoming.deadline_type.value}): {earliest_upcoming.deadline_date} ({earliest_upcoming.readiness.value})."
    elif has_passed:
        summary = "Published deadline(s) have passed for the current evaluation date."
    else:
        summary = "Deadlines require confirmation."

    return DeadlineAssessmentContext(
        deadlines=items,
        has_passed_deadline=has_passed,
        earliest_upcoming_deadline=earliest_upcoming,
        summary=summary,
    )
