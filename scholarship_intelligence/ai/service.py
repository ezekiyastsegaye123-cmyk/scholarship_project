"""AI Counselor Service coordinating context construction, model execution, safety validation, and deterministic fallbacks."""
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from scholarship_intelligence.ai.context_builder import CounselorContextBuilder
from scholarship_intelligence.ai.fallback import generate_deterministic_fallback
from scholarship_intelligence.ai.providers.base import BaseAIProvider
from scholarship_intelligence.ai.providers.factory import get_ai_provider
from scholarship_intelligence.ai.schemas import (
    AICounselorResponse,
    ChatMessage,
    CounselorContext,
    SourceCitation,
)
from scholarship_intelligence.ai.validator import validate_ai_output
from scholarship_intelligence.counselor.service import ScholarshipCounselorService
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult
from scholarship_intelligence.schemas.eligibility_eval import EligibilityEvaluationResult

logger = logging.getLogger(__name__)


class AICounselorService:
    """Service providing grounded, explainable qualitative scholarship guidance."""

    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or get_ai_provider()
        self.evaluator = EligibilityEvaluator()
        self.counselor = ScholarshipCounselorService()

    def counsel_with_context(
        self,
        context: CounselorContext,
        user_message: str,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> AICounselorResponse:
        """Generates guidance given a pre-built, verified CounselorContext."""
        history = conversation_history or []

        try:
            raw_answer = self.provider.generate_response(context, user_message, history)
            is_valid, failure_reason = validate_ai_output(raw_answer, context)

            if not is_valid:
                logger.warning("AI output validation failed: %s. Using deterministic fallback.", failure_reason)
                return generate_deterministic_fallback(context, reason=failure_reason or "Output validation failure")

            # Grounded response assembly
            known_facts = list(context.satisfied_rules)
            if context.funding_classification != "UNKNOWN":
                known_facts.append(f"Funding: {context.funding_classification}")
            if context.earliest_deadline:
                known_facts.append(f"Earliest deadline: {context.earliest_deadline}")

            return AICounselorResponse(
                answer=raw_answer,
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
                is_fallback=False,
            )
        except Exception as exc:
            logger.error("Error invoking AI provider: %s. Using deterministic fallback.", exc, exc_info=True)
            return generate_deterministic_fallback(context, reason=f"Provider exception: {str(exc)}")

    def counsel_opportunity(
        self,
        session: Session,
        opportunity_id: str,
        student_profile: Any,
        user_message: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        reference_date: Optional[date] = None,
        evaluated_at: Optional[datetime] = None,
    ) -> AICounselorResponse:
        """Fetches opportunity from DB, runs deterministic intelligence pipeline, and generates guidance."""
        opp = (
            session.query(ScholarshipOpportunity)
            .options(
                joinedload(ScholarshipOpportunity.award).selectinload(
                    getattr(ScholarshipOpportunity, "award").property.mapper.class_.funding_components
                ),
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

        # Ensure student_profile is dict
        profile_dict = student_profile if isinstance(student_profile, dict) else (
            student_profile.model_dump() if hasattr(student_profile, "model_dump") else student_profile.__dict__
        )

        target_cycle = getattr(opp, "academic_cycle", "2026-2027") or "2026-2027"

        # 1. Deterministic eligibility evaluation
        elig_res = self.evaluator.evaluate_opportunity(
            opportunity=opp,
            student_profile=profile_dict,
            target_academic_cycle=target_cycle,
            allow_partially_verified=True,
            evaluated_at=evaluated_at,
        )

        # 2. Deterministic counselor assessment
        ref = reference_date or date(2026, 11, 1)
        counselor_res = self.counselor.assess_opportunity(
            student_profile=profile_dict,
            opportunity=opp,
            eligibility_result=elig_res,
            reference_date=ref,
            evaluated_at=evaluated_at,
        )

        # 3. Assemble bounded context
        context = CounselorContextBuilder.build(
            opportunity=opp,
            student_profile=profile_dict,
            eligibility_result=elig_res,
            counselor_assessment=counselor_res,
        )

        # 4. Invoke grounded counselor
        return self.counsel_with_context(
            context=context,
            user_message=user_message,
            conversation_history=conversation_history,
        )
