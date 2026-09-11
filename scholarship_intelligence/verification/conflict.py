"""Deterministic conflict detection, representation, and resolution engine."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from scholarship_intelligence.domain.enums import (
    AuthorityTier,
    ConflictStatus,
    VerificationState,
)
from scholarship_intelligence.schemas.candidate import CandidateEvidence
from scholarship_intelligence.schemas.verification import ConflictRecordCreate
from scholarship_intelligence.verification.authority import compare_authority


class ConflictResolutionOutcome:
    """Result of evaluating a detected conflict."""

    def __init__(
        self,
        is_resolved: bool,
        winning_value: Optional[Any],
        winning_tier: Optional[AuthorityTier],
        winning_url: Optional[str],
        resolution_status: ConflictStatus,
        rationale: str,
        conflict_record: ConflictRecordCreate,
    ):
        self.is_resolved = is_resolved
        self.winning_value = winning_value
        self.winning_tier = winning_tier
        self.winning_url = winning_url
        self.resolution_status = resolution_status
        self.rationale = rationale
        self.conflict_record = conflict_record


class ConflictEngine:
    """Detects and deterministically resolves discrepancies across material scholarship facts."""

    @classmethod
    def detect_fact_discrepancy(
        cls,
        field_name: str,
        val_a: Any,
        val_b: Any,
    ) -> bool:
        """Determines if two values represent a material disagreement.
        
        UNKNOWN values do not contradict known values (UNKNOWN means unmentioned).
        """
        if val_a is None or val_b is None:
            return False

        str_a = (val_a.value if hasattr(val_a, "value") else str(val_a)).strip()
        str_b = (val_b.value if hasattr(val_b, "value") else str(val_b)).strip()

        # If either is UNKNOWN, it is lack of information, not a contradictory conflict
        if str_a.upper() in ("UNKNOWN", "TRISTATE.UNKNOWN") or str_b.upper() in ("UNKNOWN", "TRISTATE.UNKNOWN"):
            return False

        return str_a.lower() != str_b.lower()


    @classmethod
    def resolve_conflict(
        cls,
        field_name: str,
        value_a: Any,
        source_a_url: str,
        source_a_tier: AuthorityTier,
        source_a_evidence: str,
        cycle_a: Optional[str],
        value_b: Any,
        source_b_url: str,
        source_b_tier: AuthorityTier,
        source_b_evidence: str,
        cycle_b: Optional[str],
        current_cycle: str = "2026-2027",
    ) -> ConflictResolutionOutcome:
        """Deterministically resolves a conflict based on authority hierarchy and academic cycle recency.
        
        Rules:
        1. Higher authority tier outranks lower authority tier.
        2. If equal authority, current academic cycle outranks prior cycle.
        3. If equal authority and same cycle, conflict remains UNRESOLVED (OPEN).
        """
        cmp_tier = compare_authority(source_a_tier, source_b_tier)
        str_val_a = value_a.value if hasattr(value_a, "value") else str(value_a)
        str_val_b = value_b.value if hasattr(value_b, "value") else str(value_b)

        if cmp_tier < 0:
            # Source A has higher authority
            rationale = (
                f"Official source ({source_a_tier.value}) takes precedence over "
                f"lower authority source ({source_b_tier.value}) for field '{field_name}'."
            )
            conflict_rec = ConflictRecordCreate(
                field_name=field_name,
                source_a_value=str_val_a,
                source_a_url=source_a_url,
                source_a_tier=source_a_tier,
                source_a_evidence=source_a_evidence,
                source_b_value=str_val_b,
                source_b_url=source_b_url,
                source_b_tier=source_b_tier,
                source_b_evidence=source_b_evidence,
                resolution_status=ConflictStatus.RESOLVED_OFFICIAL_PREFERRED,
                resolution_notes=rationale,
                resolved_at=datetime.now(timezone.utc),
            )

            return ConflictResolutionOutcome(
                is_resolved=True,
                winning_value=value_a,
                winning_tier=source_a_tier,
                winning_url=source_a_url,
                resolution_status=ConflictStatus.RESOLVED_OFFICIAL_PREFERRED,
                rationale=rationale,
                conflict_record=conflict_rec,
            )

        elif cmp_tier > 0:
            # Source B has higher authority
            rationale = (
                f"Official source ({source_b_tier.value}) takes precedence over "
                f"lower authority source ({source_a_tier.value}) for field '{field_name}'."
            )
            conflict_rec = ConflictRecordCreate(
                field_name=field_name,
                source_a_value=str_val_a,
                source_a_url=source_a_url,
                source_a_tier=source_a_tier,
                source_a_evidence=source_a_evidence,
                source_b_value=str_val_b,
                source_b_url=source_b_url,
                source_b_tier=source_b_tier,
                source_b_evidence=source_b_evidence,
                resolution_status=ConflictStatus.RESOLVED_OFFICIAL_PREFERRED,
                resolution_notes=rationale,
                resolved_at=datetime.now(timezone.utc),
            )
            return ConflictResolutionOutcome(
                is_resolved=True,
                winning_value=value_b,
                winning_tier=source_b_tier,
                winning_url=source_b_url,
                resolution_status=ConflictStatus.RESOLVED_OFFICIAL_PREFERRED,
                rationale=rationale,
                conflict_record=conflict_rec,
            )

        # Equal authority tiers: Check cycle recency
        if cycle_a == current_cycle and cycle_b != current_cycle:
            rationale = (
                f"Source A corresponds to current academic cycle ({cycle_a}) and takes precedence "
                f"over older cycle ({cycle_b}) from source B for field '{field_name}'."
            )
            conflict_rec = ConflictRecordCreate(
                field_name=field_name,
                source_a_value=str_val_a,
                source_a_url=source_a_url,
                source_a_tier=source_a_tier,
                source_a_evidence=source_a_evidence,
                source_b_value=str_val_b,
                source_b_url=source_b_url,
                source_b_tier=source_b_tier,
                source_b_evidence=source_b_evidence,
                resolution_status=ConflictStatus.RESOLVED_RECENCY_PREFERRED,
                resolution_notes=rationale,
                resolved_at=datetime.now(timezone.utc),
            )
            return ConflictResolutionOutcome(
                is_resolved=True,
                winning_value=value_a,
                winning_tier=source_a_tier,
                winning_url=source_a_url,
                resolution_status=ConflictStatus.RESOLVED_RECENCY_PREFERRED,
                rationale=rationale,
                conflict_record=conflict_rec,
            )
        elif cycle_b == current_cycle and cycle_a != current_cycle:
            rationale = (
                f"Source B corresponds to current academic cycle ({cycle_b}) and takes precedence "
                f"over older cycle ({cycle_a}) from source A for field '{field_name}'."
            )
            conflict_rec = ConflictRecordCreate(
                field_name=field_name,
                source_a_value=str_val_a,
                source_a_url=source_a_url,
                source_a_tier=source_a_tier,
                source_a_evidence=source_a_evidence,
                source_b_value=str_val_b,
                source_b_url=source_b_url,
                source_b_tier=source_b_tier,
                source_b_evidence=source_b_evidence,
                resolution_status=ConflictStatus.RESOLVED_RECENCY_PREFERRED,
                resolution_notes=rationale,
                resolved_at=datetime.now(timezone.utc),
            )
            return ConflictResolutionOutcome(
                is_resolved=True,
                winning_value=value_b,
                winning_tier=source_b_tier,
                winning_url=source_b_url,
                resolution_status=ConflictStatus.RESOLVED_RECENCY_PREFERRED,
                rationale=rationale,
                conflict_record=conflict_rec,
            )

        # Equal authority and equal cycle: Unresolved conflict!
        rationale = (
            f"Unresolvable conflict between sources of equal authority ({source_a_tier.value}) "
            f"for academic cycle ({cycle_a or 'unknown'}). Both sources preserved. Status OPEN."
        )
        conflict_rec = ConflictRecordCreate(
            field_name=field_name,
            source_a_value=str_val_a,
            source_a_url=source_a_url,
            source_a_tier=source_a_tier,
            source_a_evidence=source_a_evidence,
            source_b_value=str_val_b,
            source_b_url=source_b_url,
            source_b_tier=source_b_tier,
            source_b_evidence=source_b_evidence,
            resolution_status=ConflictStatus.OPEN,
            resolution_notes=rationale,
            resolved_at=None,
        )

        return ConflictResolutionOutcome(
            is_resolved=False,
            winning_value=None,
            winning_tier=None,
            winning_url=None,
            resolution_status=ConflictStatus.OPEN,
            rationale=rationale,
            conflict_record=conflict_rec,
        )
