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
                details.append("Student GPA is not provided on profile; academic alignment cannot be confirmed against published minimum requirement.")
            else:
                details.append("Grading scale mismatch without defined conversion rule; academic alignment cannot be confirmed.")
        else:
            level = AlignmentLevel.NOT_ASSESSABLE
            details.append(f"Academic requirement evaluated to {target_rule.status.value}.")
    else:
        # No explicit GPA rule published
        level = AlignmentLevel.NOT_ASSESSABLE
        details.append(
            "The opportunity does not publish a minimum GPA requirement, so the system cannot determine academic alignment from GPA alone."
        )

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
            level = AlignmentLevel.NOT_ASSESSABLE
            details.append("Opportunity is verified as open to international applicants without regional restrictions.")
        elif intl_allowed == TriState.NO.value:
            level = AlignmentLevel.LIMITED
            details.append("Opportunity does not permit international students.")
        else:
            level = AlignmentLevel.UNKNOWN
            details.append("No geographic or nationality eligibility rules were extracted or published; confirm international student eligibility directly with the provider.")

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
        is_open_to_all = getattr(opportunity, "is_open_to_all_majors", False)
        if is_open_to_all:
            level = AlignmentLevel.NOT_ASSESSABLE
            details.append("Opportunity is explicitly published as open across all undergraduate fields of study.")
        else:
            level = AlignmentLevel.UNKNOWN
            details.append("No specific field-of-study restriction was extracted or published; confirm eligible academic programs directly with the provider.")

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
    """Evaluates student testing preparedness for SAT/ACT and English exams using verified provider requirements."""
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

    # Check for explicit test rules in eligibility evaluations
    test_rules: List[RuleEvaluationResult] = []
    all_rules = (
        eligibility_result.satisfied_rules
        + eligibility_result.failed_rules
        + eligibility_result.unknown_rules
        + eligibility_result.conflicting_rules
    )
    for r in all_rules:
        if r.field and any(k in r.field.lower() for k in ("sat", "act", "standardized_test")):
            test_rules.append(r)
        elif r.sub_results:
            for sub in r.sub_results:
                if sub.field and any(k in sub.field.lower() for k in ("sat", "act", "standardized_test")):
                    test_rules.append(sub)

    for r in test_rules:
        if r.evidence_snippet:
            evidence.append(r.evidence_snippet)

    # 1. Standardized tests confirmed NOT required
    if req_sat == TriState.NO and req_act == TriState.NO:
        level = ReadinessLevel.NOT_APPLICABLE
        details.append("Standardized testing (SAT/ACT) is confirmed not required for this scholarship.")
    # 2. Testing requirements are UNKNOWN
    elif req_sat == TriState.UNKNOWN and req_act == TriState.UNKNOWN and not test_rules:
        level = ReadinessLevel.UNKNOWN
        details.append("Provider standardized testing requirements are unconfirmed or under review.")
    # 3. Testing is required by flag or verified rule
    elif req_sat == TriState.YES or req_act == TriState.YES or test_rules:
        has_score = (sat_score is not None) or (act_score is not None)

        if test_rules:
            target_test_rule = test_rules[0]
            if target_test_rule.status == TriState.YES:
                level = ReadinessLevel.READY
                details.append(
                    f"Student test score satisfies published requirement ({target_test_rule.field}: expected {target_test_rule.expected_value}, actual {target_test_rule.actual_value})."
                )
            elif target_test_rule.status == TriState.NO:
                level = ReadinessLevel.NEEDS_PREPARATION
                details.append(
                    f"Student test score does not satisfy published requirement ({target_test_rule.field}: expected {target_test_rule.expected_value}, actual {target_test_rule.actual_value})."
                )
            else:
                level = ReadinessLevel.NEEDS_PREPARATION if not has_score else ReadinessLevel.PARTIALLY_READY
                details.append(
                    f"Standardized test requirement status is indeterminate ({target_test_rule.status.value})."
                )
        else:
            # Tests are required, but provider publishes no specific minimum score threshold
            if has_score:
                level = ReadinessLevel.READY
                details.append(f"Standardized testing is required and student has completed the exam (SAT: {sat_score}, ACT: {act_score}).")
            else:
                level = ReadinessLevel.NEEDS_PREPARATION
                details.append("Standardized tests (SAT/ACT) are required by the provider, but no scores are recorded on the student profile.")
    else:
        # Partial information
        level = ReadinessLevel.UNKNOWN
        details.append("Provider standardized testing policy is partially unconfirmed.")

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


DISALLOWED_EVIDENCE_PLACEHOLDERS = {
    "primary authoritative opportunity source",
    "verified source",
    "funding evidence",
    "official source",
    "official provider source",
    "placeholder",
    "none",
    "null",
    "n/a",
    "unknown",
}


def is_genuine_evidence(snippet: Any) -> bool:
    """Checks whether an evidence snippet is genuine and non-placeholder."""
    if not isinstance(snippet, str):
        return False
    cleaned = snippet.strip()
    if not cleaned:
        return False
    if cleaned.lower() in DISALLOWED_EVIDENCE_PLACEHOLDERS:
        return False
    return True


def assess_funding(opportunity: Any) -> FundingAssessmentContext:
    """Decomposes verified funding and enforces substantiated coverage with genuine evidence for full funding."""
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

    # Map component types and separate components by genuine evidence substantiation
    comp_types = set()
    substantiated_comp_types = set()
    evidence: List[str] = []

    for c in components:
        raw_t = getattr(c, "component_type", None)
        if isinstance(raw_t, FundingComponentType):
            t_val = raw_t.value
        elif isinstance(raw_t, str):
            t_val = raw_t
        else:
            t_val = None

        if t_val:
            comp_types.add(t_val)

        snippet = getattr(c, "source_evidence_snippet", None)
        if is_genuine_evidence(snippet):
            if t_val:
                substantiated_comp_types.add(t_val)
            evidence.append(snippet.strip())

    # Component existence
    has_tuition_comp = FundingComponentType.TUITION.value in comp_types
    has_room_comp = FundingComponentType.ROOM.value in comp_types
    has_meals_comp = FundingComponentType.MEALS.value in comp_types
    has_living_comp = FundingComponentType.LIVING_EXPENSES.value in comp_types
    has_stipend_comp = FundingComponentType.STIPEND.value in comp_types

    # Component substantiation (genuine supporting evidence required)
    has_substantiated_tuition = FundingComponentType.TUITION.value in substantiated_comp_types
    has_substantiated_room = FundingComponentType.ROOM.value in substantiated_comp_types
    has_substantiated_meals = FundingComponentType.MEALS.value in substantiated_comp_types
    has_substantiated_living = FundingComponentType.LIVING_EXPENSES.value in substantiated_comp_types
    has_substantiated_stipend = FundingComponentType.STIPEND.value in substantiated_comp_types

    # Substantive living support requires verified room and board/meals, or verified comprehensive living expenses/stipend
    has_substantiated_comprehensive_living = (
        (has_substantiated_room and has_substantiated_meals)
        or has_substantiated_living
        or (has_substantiated_stipend and (has_substantiated_room or has_substantiated_meals))
    )

    tuition = TriState.YES if has_substantiated_tuition else TriState.UNKNOWN
    fees = TriState.YES if FundingComponentType.MANDATORY_FEES.value in substantiated_comp_types else TriState.UNKNOWN
    room = TriState.YES if has_substantiated_room else TriState.UNKNOWN
    meals = TriState.YES if has_substantiated_meals else TriState.UNKNOWN
    living = TriState.YES if (has_substantiated_living or (has_substantiated_room and has_substantiated_meals)) else TriState.UNKNOWN
    stipend = TriState.YES if has_substantiated_stipend else TriState.UNKNOWN
    insurance = TriState.YES if FundingComponentType.HEALTH_INSURANCE.value in substantiated_comp_types else TriState.UNKNOWN
    books = TriState.YES if FundingComponentType.BOOKS.value in substantiated_comp_types else TriState.UNKNOWN
    travel = TriState.YES if FundingComponentType.TRAVEL.value in substantiated_comp_types else TriState.UNKNOWN

    details: List[str] = []

    # Strict Invariant: Full Funding requires verified tuition evidence AND verified comprehensive living evidence
    if classification == FundingClassification.FULL_FUNDING:
        if has_substantiated_tuition and has_substantiated_comprehensive_living:
            summary = "Full funding: Verified coverage includes tuition as well as living, room, and board expenses."
            details.append("Covers full cost of attendance including tuition and living expenses substantiated by official evidence.")
        elif has_substantiated_tuition:
            # Downgrade label from FULL_FUNDING to FULL_TUITION because living components lack genuine evidence
            classification = FundingClassification.FULL_TUITION
            summary = "Full tuition only: Tuition is covered. Room, meals, and living expenses are NOT verified as covered; student must plan for living costs."
            details.append("Provider award is labeled full funding, but verified components do not substantiate comprehensive room and meal expenses with genuine evidence.")
        elif has_tuition_comp and (has_room_comp or has_meals_comp or has_living_comp):
            # Components exist but lack genuine evidence (missing or placeholder)
            classification = FundingClassification.PARTIAL_FUNDING
            summary = "Unconfirmed full funding: Award components are listed but lack genuine source evidence to substantiate tuition and living coverage."
            details.append("Award components (tuition/living) are unevidenced or cite placeholder text; direct verification with provider required.")
        else:
            classification = FundingClassification.PARTIAL_FUNDING
            summary = "Partial funding: Coverage components do not substantiate complete tuition and living costs."
            details.append("Award components are incomplete or unverified.")
    elif classification == FundingClassification.FULL_TUITION:
        summary = "Full tuition only: Tuition is covered. Room, meals, and living expenses are NOT verified as covered; student must plan for living costs."
        if has_substantiated_tuition:
            details.append("Covers 100% tuition. Living, housing, and meal expenses are unconfirmed or student-funded.")
        else:
            details.append("Tuition coverage is unevidenced or missing supporting source excerpts.")
    elif classification == FundingClassification.PARTIAL_FUNDING:
        summary = "Partial funding: Provides a partial contribution toward tuition or attendance costs."
        details.append("Student must secure remaining institutional or private funds.")
    elif has_substantiated_tuition and not has_substantiated_comprehensive_living:
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
    """Evaluates readiness of application materials against student preparation status."""
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

    # Inspect profile for document preparation state
    prepared_raw = None
    if isinstance(profile, dict):
        if "prepared_materials" in profile:
            prepared_raw = profile["prepared_materials"]
        elif "application_materials" in profile:
            prepared_raw = profile["application_materials"]
        elif "completed_application_items" in profile:
            prepared_raw = profile["completed_application_items"]
    else:
        for attr in ("prepared_materials", "application_materials", "completed_application_items"):
            val = getattr(profile, attr, None)
            if val is not None:
                prepared_raw = val
                break

    if not required_components:
        level = ReadinessLevel.NOT_APPLICABLE
        missing_components: List[str] = []
        details.append("No specialized application materials or essays published by the provider.")
    elif prepared_raw is None:
        # Profile does not record preparation status: epistemic UNKNOWN
        level = ReadinessLevel.UNKNOWN
        missing_components = []
        details.append(
            f"{len(required_components)} mandatory application document(s) published by provider: {required_components}. Student document preparation status is unrecorded."
        )
    else:
        # Profile provided prepared materials list: truly evaluate readiness
        prepared_set = {str(item).strip().lower() for item in prepared_raw}
        missing = []
        for rc in required_components:
            rc_lower = rc.strip().lower()
            if not any(rc_lower in p or p in rc_lower for p in prepared_set):
                missing.append(rc)

        missing_components = missing
        if not missing:
            level = ReadinessLevel.READY
            details.append(f"All required application documents ({required_components}) are marked as prepared.")
        elif len(missing) < len(required_components):
            level = ReadinessLevel.PARTIALLY_READY
            details.append(
                f"Student has prepared {len(required_components) - len(missing)} of {len(required_components)} required documents. Pending: {missing}."
            )
        else:
            level = ReadinessLevel.NEEDS_PREPARATION
            details.append(
                f"None of the required application documents ({required_components}) are currently marked as prepared."
            )

    return ApplicationReadinessContext(
        level=level,
        total_requirements_count=total,
        required_components=required_components,
        optional_components=optional_components,
        missing_components=missing_components,
        details=details,
        evidence_snippets=evidence,
    )


def assess_deadlines(
    opportunity: Any,
    reference_date: Optional[date] = None,
) -> DeadlineAssessmentContext:
    """Evaluates multiple distinct deadlines with deterministic closing-soon threshold (14 days).

    Raises:
        ValueError: If reference_date is missing or not a date. Silent fallback
            to machine clock (date.today()) is strictly prohibited.
    """
    if reference_date is None or not isinstance(reference_date, date):
        raise ValueError("reference_date is required for deterministic deadline assessment; machine-clock fallback is prohibited")
    ref_date = reference_date
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
