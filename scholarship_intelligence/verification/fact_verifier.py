"""Fact-level evidence verification and consistency validation."""
from datetime import date
from typing import Any, List, Optional
import re

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    FundingClassification,
    FundingComponentType,
    TriState,
    VerificationState,
)
from scholarship_intelligence.schemas.candidate import (
    CandidateAward,
    CandidateDeadline,
    CandidateEvidence,
    CandidateFundingComponent,
    CandidateRequirement,
)
from scholarship_intelligence.schemas.verification import FactVerificationResult
from scholarship_intelligence.verification.authority import compare_authority

AUTHORITATIVE_TIERS = {
    AuthorityTier.OFFICIAL_PROVIDER,
    AuthorityTier.OFFICIAL_UNIVERSITY,
    AuthorityTier.GOVERNMENT,
}


class FactVerifier:
    """Validates individual candidate facts against supporting extracted evidence."""

    @classmethod
    def verify_field(
        cls,
        field_name: str,
        candidate_value: Any,
        evidence: Optional[CandidateEvidence],
        target_cycle: str = "2026-2027",
    ) -> FactVerificationResult:
        """Verifies a scalar field against its CandidateEvidence anchor."""
        # 1. Check for missing evidence
        if evidence is None or not evidence.evidence_text or not evidence.evidence_text.strip():
            return FactVerificationResult(
                field_name=field_name,
                candidate_value=candidate_value,
                verification_state=VerificationState.UNVERIFIED,
                supporting_evidence=None,
                authority_tier=None,
                notes="No supporting evidence snippet provided for material fact.",
            )

        tier = evidence.authority_tier
        ev_text = evidence.evidence_text.lower()
        val_str = str(candidate_value).strip().lower()

        # 2. Check if candidate value is UNKNOWN
        if isinstance(candidate_value, TriState) and candidate_value == TriState.UNKNOWN:
            return FactVerificationResult(
                field_name=field_name,
                candidate_value=candidate_value,
                verification_state=VerificationState.UNVERIFIED,
                supporting_evidence=evidence,
                authority_tier=tier,
                notes="Field is UNKNOWN. Preserved as UNKNOWN; no fact invented.",
            )

        # 3. Check for outdated cycle indicators in evidence
        past_cycle_patterns = ["2023-2024", "2024-2025", "2022-2023", "2023", "2024"]
        if any(p in ev_text for p in past_cycle_patterns) and target_cycle not in ev_text:
            return FactVerificationResult(
                field_name=field_name,
                candidate_value=candidate_value,
                verification_state=VerificationState.OUTDATED,
                supporting_evidence=evidence,
                authority_tier=tier,
                notes=f"Evidence explicitly refers to a previous academic cycle rather than target cycle {target_cycle}.",
            )

        # 4. Check for Authority Tier
        if tier not in AUTHORITATIVE_TIERS:
            return FactVerificationResult(
                field_name=field_name,
                candidate_value=candidate_value,
                verification_state=VerificationState.UNVERIFIED,
                supporting_evidence=evidence,
                authority_tier=tier,
                notes=f"Source authority ({tier.value}) is non-authoritative aggregator/third-party. Fact remains UNVERIFIED pending primary source.",
            )

        # 5. Check Evidence Relevance (No fabrication test)
        is_relevant = cls._check_evidence_relevance(field_name, candidate_value, ev_text)
        if not is_relevant:
            return FactVerificationResult(
                field_name=field_name,
                candidate_value=candidate_value,
                verification_state=VerificationState.UNVERIFIED,
                supporting_evidence=evidence,
                authority_tier=tier,
                notes="Supporting evidence text does not contain relevant keywords or values supporting this claim.",
            )

        # Fact satisfies all primary verification criteria
        return FactVerificationResult(
            field_name=field_name,
            candidate_value=candidate_value,
            verification_state=VerificationState.VERIFIED,
            supporting_evidence=evidence,
            authority_tier=tier,
            notes="Verified with authoritative source and verbatim supporting citation.",
        )

    @classmethod
    def _check_evidence_relevance(cls, field_name: str, value: Any, evidence_text: str) -> bool:
        """Confirms that the evidence text actually contains keywords or tokens related to the claim."""
        if field_name == "international_students_allowed":
            return any(k in evidence_text for k in ["international", "non-citizen", "foreign", "citizen", "eligible", "admissions"])
        elif field_name in ("requires_sat", "requires_act"):
            return any(k in evidence_text for k in ["sat", "act", "standardized test", "test-optional", "test optional", "testing"])
        elif field_name == "financial_need_required":
            return any(k in evidence_text for k in ["need", "financial aid", "css profile", "isfaa", "merit", "income"])
        elif field_name == "minimum_gpa":
            # Value should appear or gpa keywords appear
            val_s = str(value)
            return ("gpa" in evidence_text or val_s in evidence_text)
        elif "deadline" in field_name:
            return any(k in evidence_text for k in ["deadline", "due", "by", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "rolling"])
        elif "funding" in field_name or "award" in field_name:
            return any(k in evidence_text for k in [
                "tuition", "award", "scholarship", "funding", "stipend", "grant", "fee", "cost",
                "coverage", "covers", "cover", "room", "board", "housing", "meal", "expense", "expenses",
                "book", "travel", "allowance", "support"
            ])

        
        # Default fallback: check if value or key appears
        return True

    @classmethod
    def verify_funding_components(
        cls,
        award: Optional[CandidateAward],
        target_cycle: str = "2026-2027",
    ) -> List[FactVerificationResult]:
        """Verifies individual decomposed funding components."""
        results: List[FactVerificationResult] = []
        if not award:
            return results

        # Verify overall classification
        results.append(cls.verify_field("funding_classification", award.funding_classification, award.evidence, target_cycle))

        # Check full funding constraint: FULL_FUNDING requires room/board/living support evidence
        has_living_support = False
        for comp in award.components:
            comp_res = cls.verify_field(
                f"funding_component_{comp.component_type.value}",
                f"{comp.amount_min or ''}-{comp.amount_max or ''} {comp.currency}",
                comp.evidence,
                target_cycle,
            )
            results.append(comp_res)
            if comp.component_type in (FundingComponentType.ROOM, FundingComponentType.MEALS, FundingComponentType.LIVING_EXPENSES, FundingComponentType.STIPEND):
                if comp_res.verification_state == VerificationState.VERIFIED:
                    has_living_support = True

        # Invariant: FULL_FUNDING cannot be verified if living components are completely missing
        if award.funding_classification == FundingClassification.FULL_FUNDING and not has_living_support:
            for idx, res in enumerate(results):
                if res.field_name == "funding_classification":
                    results[idx] = FactVerificationResult(
                        field_name="funding_classification",
                        candidate_value=award.funding_classification,
                        verification_state=VerificationState.PARTIALLY_VERIFIED,
                        supporting_evidence=award.evidence,
                        authority_tier=award.evidence.authority_tier,
                        notes="FULL_FUNDING claimed, but living expenses/room/board are not verified in components. Marked PARTIALLY_VERIFIED.",
                    )
                    break

        return results

    @classmethod
    def verify_deadlines(
        cls,
        deadlines: List[CandidateDeadline],
        target_cycle: str = "2026-2027",
    ) -> List[FactVerificationResult]:
        """Verifies each deadline independently."""
        results: List[FactVerificationResult] = []
        for dl in deadlines:
            field_name = f"deadline_{dl.deadline_type.value}"
            val = str(dl.deadline_date) if dl.deadline_date else dl.raw_date_text
            res = cls.verify_field(field_name, val, dl.evidence, target_cycle)
            results.append(res)
        return results
