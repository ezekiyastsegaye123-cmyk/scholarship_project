"""Granular fact-level and content-level change detection."""
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.schemas.candidate import CandidateOpportunity
from scholarship_intelligence.verification.content_comparator import ContentComparator


class FactDifference(BaseModel):
    """Detailed record of a single fact discrepancy between canonical and candidate data."""
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    old_evidence_quote: Optional[str] = None
    new_evidence_quote: Optional[str] = None
    change_type: str = "MODIFIED"  # MODIFIED, ADDED, REMOVED


class FactComparisonResult(BaseModel):
    """Overall outcome of comparing a freshly extracted candidate against existing canonical record."""
    has_fact_changes: bool
    differences: List[FactDifference] = Field(default_factory=list)
    content_changed: bool
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    summary: str


class ChangeDetector:
    """Detects content hash changes and granular fact differences."""

    @staticmethod
    def compare_content_hashes(old_hash: Optional[str], new_hash: str):
        """Compares content SHA-256 digests via ContentComparator."""
        return ContentComparator.compare(old_hash, new_hash)

    @classmethod
    def compare_facts(
        cls,
        canonical_opp: Optional[ScholarshipOpportunity],
        candidate: CandidateOpportunity,
        old_hash: Optional[str] = None,
        new_hash: Optional[str] = None,
    ) -> FactComparisonResult:
        """Performs deep comparison across all scholarship facts."""
        content_comp = cls.compare_content_hashes(old_hash, new_hash) if new_hash else None
        content_changed = content_comp.content_changed if content_comp else True

        if canonical_opp is None:
            return FactComparisonResult(
                has_fact_changes=True,
                differences=[
                    FactDifference(
                        field_name="opportunity",
                        old_value=None,
                        new_value=candidate.title,
                        change_type="ADDED",
                    )
                ],
                content_changed=content_changed,
                old_hash=old_hash,
                new_hash=new_hash,
                summary="New opportunity candidate; baseline facts established.",
            )

        differences: List[FactDifference] = []
        candidate_primary_ev = candidate.source_evidence[0] if candidate.source_evidence else None
        candidate_quote = candidate_primary_ev.evidence_text if candidate_primary_ev else None
        
        canonical_ev_quote = None
        if canonical_opp.official_sources:
            canonical_ev_quote = canonical_opp.official_sources[0].extracted_text_snippet

        # 1. Compare Scalar Fields
        scalar_fields = [
            ("international_students_allowed", canonical_opp.international_students_allowed, candidate.international_students_allowed.value),
            ("requires_sat", canonical_opp.requires_sat, candidate.requires_sat.value),
            ("requires_act", canonical_opp.requires_act, candidate.requires_act.value),
            ("requires_css_profile", canonical_opp.requires_css_profile, candidate.requires_css_profile.value),
            ("financial_need_required", canonical_opp.financial_need_required, candidate.financial_need_required.value),
            ("target_degree_level", canonical_opp.target_degree_level, candidate.target_degree_level),
            ("academic_cycle", canonical_opp.academic_cycle, candidate.academic_cycle),
        ]

        for field_name, old_val, new_val in scalar_fields:
            if old_val != new_val:
                differences.append(
                    FactDifference(
                        field_name=field_name,
                        old_value=str(old_val) if old_val is not None else None,
                        new_value=str(new_val) if new_val is not None else None,
                        old_evidence_quote=canonical_ev_quote,
                        new_evidence_quote=candidate_quote,
                        change_type="MODIFIED",
                    )
                )

        # 2. Compare Deadlines
        old_dl_dates = {str(d.deadline_date) for d in canonical_opp.deadlines if d.deadline_date}
        new_dl_dates = {str(d.deadline_date) for d in candidate.deadlines if d.deadline_date}
        if old_dl_dates != new_dl_dates:
            differences.append(
                FactDifference(
                    field_name="deadlines",
                    old_value=",".join(sorted(old_dl_dates)) if old_dl_dates else None,
                    new_value=",".join(sorted(new_dl_dates)) if new_dl_dates else None,
                    old_evidence_quote=canonical_ev_quote,
                    new_evidence_quote=candidate_quote,
                    change_type="MODIFIED" if old_dl_dates else "ADDED",
                )
            )

        # 3. Compare Award Amounts
        old_award_val = canonical_opp.award.estimated_annual_value_usd if canonical_opp.award else None
        new_award_val = candidate.award.estimated_annual_value_usd if candidate.award else None
        if old_award_val != new_award_val:
            differences.append(
                FactDifference(
                    field_name="award_value_usd",
                    old_value=str(old_award_val) if old_award_val is not None else None,
                    new_value=str(new_award_val) if new_award_val is not None else None,
                    old_evidence_quote=canonical_ev_quote,
                    new_evidence_quote=candidate_quote,
                    change_type="MODIFIED",
                )
            )

        has_changes = len(differences) > 0
        summary = (
            f"Detected {len(differences)} fact differences across scalar/deadline/award attributes."
            if has_changes
            else "Content verified; zero fact differences detected."
        )

        return FactComparisonResult(
            has_fact_changes=has_changes,
            differences=differences,
            content_changed=content_changed,
            old_hash=old_hash,
            new_hash=new_hash,
            summary=summary,
        )
