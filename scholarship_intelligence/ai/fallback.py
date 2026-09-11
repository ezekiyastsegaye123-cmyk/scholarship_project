"""Deterministic fallback response generator when AI provider is unavailable or fails safety validation."""
from typing import List

from scholarship_intelligence.ai.schemas import (
    AICounselorResponse,
    CounselorContext,
    SourceCitation,
)


def generate_deterministic_fallback(
    context: CounselorContext,
    reason: str = "Automated AI provider fallback",
) -> AICounselorResponse:
    """Generates a fully grounded, deterministic counseling response directly from context facts.

    Never hallucinates, never calculates chances, and explicitly surfaces
    verified rules, gaps, epistemic uncertainties, and official sources.
    """
    provider_lbl = f" (Provider: {context.provider_name})" if context.provider_name else ""
    lines: List[str] = [
        f"### Guidance for {context.opportunity_title}{provider_lbl}",
        "",
        f"**Assessment Grounding Status:** {context.epistemic_status.value.replace('_', ' ').title()}",
        f"**Eligibility Evaluation:** {context.eligibility_status.replace('_', ' ').title()}",
        "",
    ]

    # Deadlines & Timing
    if context.deadlines:
        lines.append("**Application Deadlines:**")
        for dl in context.deadlines:
            d_date = dl.get("deadline_date") or "Ongoing / Unspecified"
            d_type = dl.get("deadline_type", "Deadline")
            lines.append(f"- {d_type}: {d_date}")
    else:
        lines.append("**Application Deadline:** Not specified or rolling.")
    lines.append("")

    # Funding Transparency
    lines.append("**Funding Overview:**")
    lines.append(f"- Classification: {context.funding_classification}")
    lines.append(f"- Tuition Coverage: {context.tuition_covered}")
    lines.append(f"- Living Expenses Covered: {context.living_expenses_covered}")
    lines.append(f"- Mandatory Fees Covered: {context.fees_covered}")
    if context.funding_summary:
        lines.append(f"- Details: {context.funding_summary}")
    lines.append("")

    # Rules Assessment
    if context.satisfied_rules:
        lines.append("**Verified Satisfied Requirements:**")
        for rule in context.satisfied_rules:
            lines.append(f"- {rule}")
        lines.append("")

    if context.failed_rules:
        lines.append("**Unmet Criteria (Actionable Gaps):**")
        for rule in context.failed_rules:
            lines.append(f"- {rule}")
        lines.append("")

    if context.unknown_rules:
        lines.append("**Criteria Requiring Student Clarification:**")
        for rule in context.unknown_rules:
            lines.append(f"- {rule}")
        lines.append("")

    # Strengths & Next steps
    if context.strengths:
        lines.append("**Key Strengths:**")
        for s in context.strengths:
            lines.append(f"- {s}")
        lines.append("")

    if context.next_steps:
        lines.append("**Recommended Next Steps:**")
        for ns in context.next_steps:
            lines.append(f"1. {ns}")
        lines.append("")

    # Epistemic note if uncertainties exist
    if context.uncertainties:
        lines.append("**Important Considerations & Uncertainties:**")
        for u in context.uncertainties:
            lines.append(f"- {u}")
        lines.append("")

    lines.append(
        "*(Note: This guidance was deterministically assembled directly from verified repository facts "
        f"due to: {reason})*"
    )

    answer_text = "\n".join(lines)

    # Known facts extracted from context
    known_facts = list(context.satisfied_rules)
    if context.funding_classification != "UNKNOWN":
        known_facts.append(f"Funding classification: {context.funding_classification}")
    if context.earliest_deadline:
        known_facts.append(f"Earliest deadline: {context.earliest_deadline}")

    return AICounselorResponse(
        answer=answer_text,
        epistemic_status=context.epistemic_status,
        warnings=list(context.warnings),
        sources=list(context.evidence_sources),
        known_facts=known_facts,
        unknowns=list(context.unknown_rules) + list(context.uncertainties),
        next_steps=list(context.next_steps),
        disclaimer=(
            "AI guidance explains the verified scholarship information available in the system. "
            "It does not determine admission or scholarship selection outcomes. "
            "Always verify important requirements and deadlines with the official source."
        ),
        is_fallback=True,
    )
