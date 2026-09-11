"""Deterministic Mock AI Counselor Provider.

Enables full offline development, automated testing, and safe demonstration
without incurring external API costs, latency, or nondeterministic flakiness.
"""
from typing import List

from scholarship_intelligence.ai.providers.base import BaseAIProvider
from scholarship_intelligence.ai.schemas import ChatMessage, CounselorContext


class MockAIProvider(BaseAIProvider):
    """Deterministic, evidence-grounded mock provider."""

    def generate_response(
        self,
        context: CounselorContext,
        user_message: str,
        conversation_history: List[ChatMessage],
    ) -> str:
        q = user_message.lower().strip()

        # ----------------------------------------------------------------------
        # 1. Adversarial & Prompt Injection Defense
        # ----------------------------------------------------------------------
        if any(term in q for term in ["system prompt", "system instructions", "reveal prompt", "initial prompt"]):
            return (
                "I am the Scholarship Intelligence AI Counselor. My role is to explain verified scholarship "
                "criteria, funding terms, and deadlines based exclusively on authoritative data from institutions."
            )

        if any(term in q for term in ["password", "secret", "api_key", "token", "database url", "credentials"]):
            return (
                "Internal system credentials, keys, and confidential security materials are strictly protected "
                "and not accessible."
            )

        if any(term in q for term in ["chance", "probability", "odds", "likely to win", "will i win", "acceptance rate"]):
            return (
                "This platform does not calculate or predict scholarship acceptance probabilities or admission odds. "
                "Selection decisions involve holistic, independent evaluation by the awarding committee. "
                f"Based on our deterministic evaluation, your eligibility status is {context.eligibility_status}, "
                f"with {context.academic_alignment.lower()} academic alignment and {context.application_readiness.lower()} application readiness."
            )

        if any(term in q for term in ["make up", "guess", "invent", "hallucinate", "pretend"]):
            return (
                "I cannot invent or assume unconfirmed requirements or deadlines. All facts provided are derived "
                "directly from verified institutional evidence."
            )

        if "ignore" in q and ("instruction" in q or "data" in q or "rules" in q or "previous" in q):
            return (
                "I cannot disregard verified scholarship data or foundational counseling rules. "
                f"I can only provide guidance grounded in the verified record for {context.opportunity_title}."
            )

        if "another student" in q or "other user" in q or "someone else" in q:
            return (
                "Student profiles are strictly confidential. I only have access to your own authenticated profile "
                "and public verified scholarship records."
            )

        # ----------------------------------------------------------------------
        # 2. Eligibility Explanation ("Why am I eligible?")
        # ----------------------------------------------------------------------
        if any(term in q for term in ["why am i eligible", "eligib", "qualify", "am i eligible"]):
            parts = [
                f"Regarding **{context.opportunity_title}**, your overall eligibility status is **{context.eligibility_status}**."
            ]

            if context.satisfied_rules:
                rules_str = "; ".join(context.satisfied_rules[:4])
                parts.append(f"Satisfied institutional criteria include: {rules_str}.")

            if context.academic_alignment != "UNKNOWN":
                parts.append(f"Academic alignment is assessed as {context.academic_alignment}.")

            if context.geographic_alignment != "UNKNOWN":
                parts.append(f"Geographic/citizenship alignment is assessed as {context.geographic_alignment}.")

            if context.unknown_rules:
                unk_str = "; ".join(context.unknown_rules[:3])
                parts.append(f"The following criteria require additional verification: {unk_str}.")

            if context.verification_status != "VERIFIED":
                parts.append(f"Note: This opportunity currently has verification status {context.verification_status}.")

            return " ".join(parts)

        # ----------------------------------------------------------------------
        # 3. Gaps & Missing Information ("What am I missing?")
        # ----------------------------------------------------------------------
        if any(term in q for term in ["missing", "gap", "lack", "need to add", "what do i need"]):
            parts = [f"Analysis of your profile against **{context.opportunity_title}**:"]

            if context.gaps:
                gaps_str = "; ".join(context.gaps)
                parts.append(f"Identified gaps: {gaps_str}.")
            elif context.failed_rules:
                failed_str = "; ".join(context.failed_rules)
                parts.append(f"Unfulfilled requirements: {failed_str}.")
            else:
                parts.append("No definitive disqualifying criteria were identified in the verified data.")

            if context.unknown_rules:
                unk_str = "; ".join(context.unknown_rules)
                parts.append(f"Unconfirmed / unknown criteria: {unk_str}.")

            if context.testing_readiness == "NEEDS_ATTENTION":
                parts.append("Standardized testing scores require attention.")

            return " ".join(parts)

        # ----------------------------------------------------------------------
        # 4. Funding & Tuition Explanation ("Does this cover tuition?")
        # ----------------------------------------------------------------------
        if any(term in q for term in ["tuition", "fund", "money", "amount", "stipend", "cover", "cost", "award"]):
            parts = [
                f"**Funding Classification**: {context.funding_classification}."
            ]
            if context.funding_summary:
                parts.append(f"Summary: {context.funding_summary}.")

            if context.funding_classification == "FULL_TUITION":
                parts.append(
                    "Important clarification: Full tuition coverage covers academic instruction fees, but does not "
                    "establish coverage of living expenses, books, healthcare, or personal costs."
                )
            elif context.funding_classification == "FULL_FUNDING":
                parts.append("Verified data indicates comprehensive coverage including tuition and living expenses.")

            if context.tuition_covered != "UNKNOWN":
                parts.append(f"Tuition covered: {context.tuition_covered}.")
            if context.living_expenses_covered != "UNKNOWN":
                parts.append(f"Living expenses covered: {context.living_expenses_covered}.")

            return " ".join(parts)

        # ----------------------------------------------------------------------
        # 5. Deadlines ("When is the deadline?")
        # ----------------------------------------------------------------------
        if any(term in q for term in ["deadline", "due date", "when to apply", "timeline", "date"]):
            if context.earliest_deadline:
                return (
                    f"The earliest confirmed deadline for **{context.opportunity_title}** is **{context.earliest_deadline}** "
                    f"(Status: {context.deadline_status})."
                )
            elif context.deadline_status == "ROLLING":
                return f"Applications for **{context.opportunity_title}** are evaluated on a rolling basis."
            else:
                return (
                    f"No exact deadline is currently published in verified institutional sources for "
                    f"**{context.opportunity_title}**. Please consult the official provider link to confirm dates."
                )

        # ----------------------------------------------------------------------
        # 6. Preparation & Next Steps ("What should I prepare?")
        # ----------------------------------------------------------------------
        if any(term in q for term in ["prepare", "document", "action", "next step", "what should i do"]):
            parts = [f"Recommended preparation actions for **{context.opportunity_title}**:"]
            if context.next_steps:
                for idx, step in enumerate(context.next_steps[:4], 1):
                    parts.append(f"{idx}. {step}")
            else:
                parts.append("1. Review official university application guidelines.")
                parts.append("2. Ensure transcripts and recommendation letters are assembled.")
            return "\n".join(parts)

        # ----------------------------------------------------------------------
        # 7. Unknowns & Unconfirmed Criteria
        # ----------------------------------------------------------------------
        if any(term in q for term in ["unknown", "unverified", "uncertain", "not sure"]):
            if context.unknown_rules or context.uncertainties:
                all_unk = context.unknown_rules + context.uncertainties
                return (
                    f"The following criteria could not be confirmed with institutional evidence: "
                    + "; ".join(all_unk[:5])
                    + ". These items should be verified directly with the awarding body."
                )
            return "All key evaluation criteria for this opportunity have been evaluated against verified facts."

        # ----------------------------------------------------------------------
        # 8. General Inquiry Synthesis
        # ----------------------------------------------------------------------
        overview = [
            f"**{context.opportunity_title}** ({context.university_name or context.provider_name or 'Institutional Award'}).",
            f"- Status: **{context.eligibility_status}** (Academic alignment: {context.academic_alignment}).",
            f"- Funding: **{context.funding_classification}**.",
            f"- Deadline: **{context.earliest_deadline or context.deadline_status}**.",
            f"- Verification: **{context.verification_status}**.",
        ]
        if context.next_steps:
            overview.append(f"Recommended next step: {context.next_steps[0]}")
        return "\n".join(overview)
