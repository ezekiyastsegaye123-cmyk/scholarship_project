"""Deterministic template-based human-readable explanation generator.

Guarantees:
- Zero LLM calls, zero probabilistic text generation.
- 100% deterministic, auditable, and reproducible.
- Cites field, expected requirement, actual student value, and source evidence provenance.
"""
from typing import Any, Optional
from scholarship_intelligence.domain.enums import RuleComparisonOp, RuleKind, TriState


def format_rule_explanation(
    status: TriState,
    kind: RuleKind,
    field: Optional[str],
    op: Optional[RuleComparisonOp],
    expected_value: Any,
    actual_value: Any,
    scale: Optional[float] = None,
    student_scale: Optional[float] = None,
    rule_id: Optional[str] = None,
    description: Optional[str] = None,
    evidence_snippet: Optional[str] = None,
) -> str:
    """Formats a deterministic human-readable explanation for a rule evaluation."""
    field_name = field or "Requirement"
    kind_prefix = f"[{kind.value}] " if kind != RuleKind.REQUIRED else ""
    rule_tag = f" (Rule: {rule_id})" if rule_id else ""

    # Provenance snippet suffix
    evidence_suffix = ""
    if evidence_snippet:
        evidence_suffix = f' [Source Evidence: "{evidence_snippet.strip()}"]'

    if status == TriState.YES:
        if scale is not None:
            text = (
                f"{kind_prefix}Satisfied: Student {field_name} of {actual_value} satisfies requirement "
                f"({op.value if op else ''} {expected_value} on {scale} scale){rule_tag}.{evidence_suffix}"
            )
        elif op == RuleComparisonOp.IN:
            text = (
                f"{kind_prefix}Satisfied: Student {field_name} '{actual_value}' is in allowed criteria "
                f"{expected_value}{rule_tag}.{evidence_suffix}"
            )
        elif op == RuleComparisonOp.CONTAINS:
            text = (
                f"{kind_prefix}Satisfied: Student {field_name} contains required item '{expected_value}'{rule_tag}.{evidence_suffix}"
            )
        else:
            text = (
                f"{kind_prefix}Satisfied: Student {field_name} '{actual_value}' meets requirement "
                f"({op.value if op else ''} {expected_value}){rule_tag}.{evidence_suffix}"
            )
        return text

    if status == TriState.NO:
        if scale is not None:
            text = (
                f"{kind_prefix}Unsatisfied: The scholarship requires {field_name} {op.value if op else ''} {expected_value} "
                f"(on {scale} scale), but student has {actual_value}{rule_tag}.{evidence_suffix}"
            )
        elif op == RuleComparisonOp.IN:
            text = (
                f"{kind_prefix}Unsatisfied: Student {field_name} '{actual_value}' is not within eligible criteria "
                f"{expected_value}{rule_tag}.{evidence_suffix}"
            )
        elif op == RuleComparisonOp.CONTAINS:
            text = (
                f"{kind_prefix}Unsatisfied: Student profile does not contain required {field_name} item '{expected_value}'{rule_tag}.{evidence_suffix}"
            )
        else:
            text = (
                f"{kind_prefix}Unsatisfied: The scholarship requires {field_name} {op.value if op else ''} {expected_value}, "
                f"but student profile has '{actual_value}'{rule_tag}.{evidence_suffix}"
            )
        return text

    if status == TriState.UNKNOWN:
        if actual_value is None:
            text = (
                f"{kind_prefix}Information Needed: The scholarship requires {field_name} "
                f"({op.value if op else ''} {expected_value}), but student's {field_name} has not been provided{rule_tag}.{evidence_suffix}"
            )
        elif scale is not None and student_scale is not None and scale != student_scale:
            text = (
                f"{kind_prefix}Information Needed: The scholarship evaluates {field_name} on a {scale} scale "
                f"({op.value if op else ''} {expected_value}), but student provided GPA on a {student_scale} scale "
                f"without an established conversion{rule_tag}.{evidence_suffix}"
            )
        else:
            text = (
                f"{kind_prefix}Information Needed: Insufficient information to determine if student satisfies "
                f"{field_name} requirement ({op.value if op else ''} {expected_value}){rule_tag}.{evidence_suffix}"
            )
        return text

    if status == TriState.CONFLICTING:
        text = (
            f"{kind_prefix}Unresolved Conflict: Student profile contains contradictory or conflicting verified "
            f"values for {field_name}{rule_tag}. Resolution is required before eligibility can be established.{evidence_suffix}"
        )
        return text

    if status == TriState.NOT_APPLICABLE:
        text = (
            f"{kind_prefix}Not Applicable: Condition on {field_name} ({op.value if op else ''} {expected_value}) "
            f"does not apply in this evaluation context{rule_tag}.{evidence_suffix}"
        )
        return text

    return f"Evaluation outcome: {status.value} for {field_name}{rule_tag}.{evidence_suffix}"
