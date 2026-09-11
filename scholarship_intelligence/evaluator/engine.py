"""Deterministic Eligibility Evaluation Engine.

Core Invariants:
- 100% Deterministic: Same profile + same rules = identical result.
- Bounded Execution: Rule AST depth <= 5, no arbitrary code execution (no eval/exec).
- Uncertainty Preservation: UNKNOWN != NO. Missing data yields UNKNOWN / NEEDS_INFORMATION.
- Verification Gating: Unverified, conflicting, outdated, or quarantined opportunities are gated.
- Academic Cycle Gating: Requires cycle match (e.g. 2026-2027).
- No Numerical Scores: No fit_score, match_score, competitiveness_score, or acceptance probabilities.
"""
from datetime import datetime, timezone
from typing import Any, List, Optional, Union

from scholarship_intelligence.domain.enums import (
    RuleComparisonOp,
    RuleKind,
    RuleLogicalOp,
    TriState,
    VerificationState,
)
from scholarship_intelligence.domain.rules import (
    ComparisonExpression,
    EligibilityRuleDefinition,
    LogicalExpression,
)
from scholarship_intelligence.evaluator.explainer import format_rule_explanation
from scholarship_intelligence.evaluator.field_registry import (
    extract_student_value,
    resolve_field_name,
)
from scholarship_intelligence.evaluator.logic import (
    evaluate_and_all,
    evaluate_not,
    evaluate_or_all,
)
from scholarship_intelligence.evaluator.operators import evaluate_comparison
from scholarship_intelligence.evaluator.validator import (
    RuleValidationError,
    validate_rule_expression,
)
from scholarship_intelligence.schemas.eligibility_eval import (
    EligibilityEvaluationResult,
    EligibilityStatus,
    RuleEvaluationResult,
)


class EligibilityEvaluator:
    """Evaluates student profiles against scholarship eligibility rules deterministically."""

    def evaluate_expression(
        self,
        expr: Any,
        student_profile: Any,
        rule_id: str = "expr",
        kind: RuleKind = RuleKind.REQUIRED,
        evidence_snippet: Optional[str] = None,
        description: Optional[str] = None,
    ) -> RuleEvaluationResult:
        """Evaluates a validated rule expression AST against a student profile."""
        # Validate AST before evaluation
        validate_rule_expression(expr)

        # 1. Comparison node
        if isinstance(expr, (ComparisonExpression, dict)) and (
            isinstance(expr, ComparisonExpression) or "field" in expr
        ):
            if isinstance(expr, ComparisonExpression):
                field = expr.field
                op = expr.op
                expected_val = expr.value
                scale = expr.scale
            else:
                field = expr["field"]
                op = RuleComparisonOp(str(expr["op"]).upper())
                expected_val = expr["value"]
                scale = expr.get("scale")

            actual_val, is_conflicting, student_scale = extract_student_value(
                student_profile, field
            )

            if is_conflicting:
                status = TriState.CONFLICTING
                explanation = format_rule_explanation(
                    status=status,
                    kind=kind,
                    field=field,
                    op=op,
                    expected_value=expected_val,
                    actual_value="[CONFLICTING]",
                    scale=scale,
                    student_scale=student_scale,
                    rule_id=rule_id,
                    description=description,
                    evidence_snippet=evidence_snippet,
                )
            else:
                status, _ = evaluate_comparison(
                    op=op,
                    field=field,
                    expected_value=expected_val,
                    actual_value=actual_val,
                    expected_scale=scale,
                    student_scale=student_scale,
                )
                explanation = format_rule_explanation(
                    status=status,
                    kind=kind,
                    field=field,
                    op=op,
                    expected_value=expected_val,
                    actual_value=actual_val,
                    scale=scale,
                    student_scale=student_scale,
                    rule_id=rule_id,
                    description=description,
                    evidence_snippet=evidence_snippet,
                )

            return RuleEvaluationResult(
                rule_id=rule_id,
                kind=kind,
                status=status,
                explanation=explanation,
                field=field,
                expected_value=expected_val,
                actual_value=actual_val,
                scale=scale,
                student_scale=student_scale,
                evidence_snippet=evidence_snippet,
                sub_results=[],
            )

        # 2. Logical composite node
        if isinstance(expr, (LogicalExpression, dict)):
            if isinstance(expr, LogicalExpression):
                log_op = expr.op
                raw_operands = expr.operands
            else:
                log_op = RuleLogicalOp(str(expr["op"]).upper())
                raw_operands = expr["operands"]

            sub_results: List[RuleEvaluationResult] = []
            for idx, child in enumerate(raw_operands):
                sub_id = f"{rule_id}.{idx + 1}"
                sub_res = self.evaluate_expression(
                    expr=child,
                    student_profile=student_profile,
                    rule_id=sub_id,
                    kind=kind,
                    evidence_snippet=evidence_snippet,
                    description=description,
                )
                sub_results.append(sub_res)

            sub_statuses = [s.status for s in sub_results]

            if log_op == RuleLogicalOp.NOT:
                overall_status = evaluate_not(sub_statuses[0])
                explanation = (
                    f"[{kind.value}] Logical NOT: Operand evaluated to {sub_statuses[0].value}, "
                    f"yielding {overall_status.value}."
                )
            elif log_op == RuleLogicalOp.AND:
                overall_status = evaluate_and_all(sub_statuses)
                explanation = (
                    f"[{kind.value}] Logical AND: Evaluated {len(sub_statuses)} conditions "
                    f"resulting in {overall_status.value}."
                )
            elif log_op == RuleLogicalOp.OR:
                overall_status = evaluate_or_all(sub_statuses)
                explanation = (
                    f"[{kind.value}] Logical OR: Evaluated {len(sub_statuses)} alternative conditions "
                    f"resulting in {overall_status.value}."
                )
            else:
                overall_status = TriState.UNKNOWN
                explanation = f"Unknown logical operator '{log_op}'."

            return RuleEvaluationResult(
                rule_id=rule_id,
                kind=kind,
                status=overall_status,
                explanation=explanation,
                field=None,
                expected_value=None,
                actual_value=None,
                evidence_snippet=evidence_snippet,
                sub_results=sub_results,
            )

        raise RuleValidationError(f"Unsupported rule expression type: {type(expr).__name__}")

    def evaluate_rule(
        self,
        rule: Any,
        student_profile: Any,
    ) -> RuleEvaluationResult:
        """Evaluates a single rule instance (SQLAlchemy model, Pydantic definition, or dict)."""
        if isinstance(rule, dict):
            rule_id = rule.get("rule_id", "rule_anon")
            kind_str = rule.get("kind", RuleKind.REQUIRED.value)
            kind = RuleKind(kind_str) if isinstance(kind_str, str) else kind_str
            expr = rule.get("expression") or rule.get("expression_json")
            evidence = rule.get("source_evidence_snippet")
            desc = rule.get("description")
        elif isinstance(rule, EligibilityRuleDefinition):
            rule_id = rule.rule_id
            kind = rule.kind
            expr = rule.expression
            evidence = rule.source_evidence_snippet
            desc = rule.description
        else:
            # SQLAlchemy model or duck-typed object
            rule_id = getattr(rule, "rule_id", "rule_model")
            raw_kind = getattr(rule, "kind", RuleKind.REQUIRED.value)
            kind = RuleKind(raw_kind) if isinstance(raw_kind, str) else raw_kind
            expr = getattr(rule, "expression_json", None) or getattr(rule, "expression", None)
            evidence = getattr(rule, "source_evidence_snippet", None)
            desc = getattr(rule, "description", None)

        return self.evaluate_expression(
            expr=expr,
            student_profile=student_profile,
            rule_id=rule_id,
            kind=kind,
            evidence_snippet=evidence,
            description=desc,
        )

    def evaluate_rules(
        self,
        rules: List[Any],
        student_profile: Any,
        opportunity_id: Optional[str] = None,
        opportunity_title: Optional[str] = None,
        target_academic_cycle: str = "2026-2027",
        opportunity_academic_cycle: Optional[str] = None,
        verification_status: Optional[VerificationState] = None,
    ) -> EligibilityEvaluationResult:
        """Evaluates a list of rules and aggregates into a final EligibilityEvaluationResult."""
        satisfied_rules: List[RuleEvaluationResult] = []
        failed_rules: List[RuleEvaluationResult] = []
        unknown_rules: List[RuleEvaluationResult] = []
        conflicting_rules: List[RuleEvaluationResult] = []
        not_applicable_rules: List[RuleEvaluationResult] = []
        supplementary_rules: List[RuleEvaluationResult] = []
        explanations: List[str] = []

        for r in rules:
            result = self.evaluate_rule(r, student_profile)
            explanations.append(result.explanation)

            if result.kind == RuleKind.REQUIRED:
                if result.status == TriState.YES:
                    satisfied_rules.append(result)
                elif result.status == TriState.NO:
                    failed_rules.append(result)
                elif result.status == TriState.UNKNOWN:
                    unknown_rules.append(result)
                elif result.status == TriState.CONFLICTING:
                    conflicting_rules.append(result)
                elif result.status == TriState.NOT_APPLICABLE:
                    not_applicable_rules.append(result)
            else:
                supplementary_rules.append(result)

        # Status aggregation logic
        if failed_rules:
            overall_status = EligibilityStatus.INELIGIBLE
            summary = (
                f"Overall Decision: INELIGIBLE. Failed {len(failed_rules)} required eligibility "
                f"condition(s)."
            )
        elif conflicting_rules:
            overall_status = EligibilityStatus.NEEDS_REVIEW
            summary = (
                f"Overall Decision: NEEDS_REVIEW. Unresolved contradictory data exists for "
                f"{len(conflicting_rules)} required condition(s)."
            )
        elif unknown_rules:
            overall_status = EligibilityStatus.NEEDS_INFORMATION
            summary = (
                f"Overall Decision: NEEDS_INFORMATION. Missing student profile data for "
                f"{len(unknown_rules)} required condition(s)."
            )
        else:
            # All required rules are YES or NOT_APPLICABLE
            overall_status = EligibilityStatus.ELIGIBLE
            summary = (
                f"Overall Decision: ELIGIBLE. Satisfied all {len(satisfied_rules)} verified "
                f"required eligibility condition(s)."
            )

        explanations.insert(0, summary)

        return EligibilityEvaluationResult(
            opportunity_id=opportunity_id,
            opportunity_title=opportunity_title,
            status=overall_status,
            target_academic_cycle=target_academic_cycle,
            opportunity_academic_cycle=opportunity_academic_cycle,
            verification_status=verification_status,
            is_gated=False,
            satisfied_rules=satisfied_rules,
            failed_rules=failed_rules,
            unknown_rules=unknown_rules,
            conflicting_rules=conflicting_rules,
            not_applicable_rules=not_applicable_rules,
            supplementary_rules=supplementary_rules,
            explanations=explanations,
            audit_metadata={
                "rules_count": len(rules),
                "required_count": len(satisfied_rules)
                + len(failed_rules)
                + len(unknown_rules)
                + len(conflicting_rules)
                + len(not_applicable_rules),
                "supplementary_count": len(supplementary_rules),
            },
        )

    def evaluate_opportunity(
        self,
        opportunity: Any,
        student_profile: Any,
        target_academic_cycle: str = "2026-2027",
        allow_partially_verified: bool = False,
    ) -> EligibilityEvaluationResult:
        """Evaluates a ScholarshipOpportunity, strictly enforcing verification gating and cycle matching."""
        opp_id = getattr(opportunity, "id", None)
        opp_title = getattr(opportunity, "title", "Untitled Opportunity")
        opp_cycle = getattr(opportunity, "academic_cycle", None)
        raw_v_status = getattr(opportunity, "verification_status", VerificationState.UNVERIFIED.value)
        v_status = VerificationState(raw_v_status) if isinstance(raw_v_status, str) else raw_v_status

        # 1. Verification-State Gating
        gated_reasons: dict[VerificationState, tuple[EligibilityStatus, str]] = {
            VerificationState.UNVERIFIED: (
                EligibilityStatus.GATED_UNVERIFIED,
                "Evaluation blocked: Opportunity eligibility rules are UNVERIFIED and cannot be reliably evaluated.",
            ),
            VerificationState.OUTDATED: (
                EligibilityStatus.GATED_UNVERIFIED,
                "Evaluation blocked: Opportunity verification is OUTDATED. Rules must be reverified before evaluation.",
            ),
            VerificationState.CONFLICTING: (
                EligibilityStatus.NEEDS_REVIEW,
                "Evaluation blocked: Opportunity contains unresolved contradictory verification evidence.",
            ),
            VerificationState.SOURCE_UNAVAILABLE: (
                EligibilityStatus.GATED_UNVERIFIED,
                "Evaluation blocked: Official source is UNAVAILABLE or inaccessible.",
            ),
            VerificationState.QUARANTINED_FOR_REVIEW: (
                EligibilityStatus.NEEDS_REVIEW,
                "Evaluation blocked: Opportunity is QUARANTINED_FOR_REVIEW due to material verification concerns.",
            ),
        }

        if v_status in gated_reasons:
            status, reason = gated_reasons[v_status]
            return EligibilityEvaluationResult(
                opportunity_id=opp_id,
                opportunity_title=opp_title,
                status=status,
                target_academic_cycle=target_academic_cycle,
                opportunity_academic_cycle=opp_cycle,
                verification_status=v_status,
                is_gated=True,
                explanations=[reason],
                audit_metadata={"gating_reason": v_status.value},
            )

        if v_status == VerificationState.PARTIALLY_VERIFIED and not allow_partially_verified:
            return EligibilityEvaluationResult(
                opportunity_id=opp_id,
                opportunity_title=opp_title,
                status=EligibilityStatus.GATED_UNVERIFIED,
                target_academic_cycle=target_academic_cycle,
                opportunity_academic_cycle=opp_cycle,
                verification_status=v_status,
                is_gated=True,
                explanations=[
                    "Evaluation blocked: Opportunity is only PARTIALLY_VERIFIED. "
                    "Evaluation requires allow_partially_verified=True flag."
                ],
                audit_metadata={"gating_reason": "PARTIALLY_VERIFIED_DISALLOWED"},
            )

        # 2. Academic-Cycle Gating
        if opp_cycle and opp_cycle != target_academic_cycle:
            return EligibilityEvaluationResult(
                opportunity_id=opp_id,
                opportunity_title=opp_title,
                status=EligibilityStatus.OUTDATED_CYCLE,
                target_academic_cycle=target_academic_cycle,
                opportunity_academic_cycle=opp_cycle,
                verification_status=v_status,
                is_gated=True,
                explanations=[
                    f"Evaluation blocked: Academic cycle mismatch. Opportunity is verified for cycle "
                    f"'{opp_cycle}', but target evaluation cycle is '{target_academic_cycle}'. "
                    f"Rules cannot be assumed valid for different academic years."
                ],
                audit_metadata={"gating_reason": "CYCLE_MISMATCH", "opportunity_cycle": opp_cycle},
            )

        # 3. Retrieve rules
        rules = getattr(opportunity, "eligibility_rules", [])
        return self.evaluate_rules(
            rules=rules,
            student_profile=student_profile,
            opportunity_id=opp_id,
            opportunity_title=opp_title,
            target_academic_cycle=target_academic_cycle,
            opportunity_academic_cycle=opp_cycle,
            verification_status=v_status,
        )
