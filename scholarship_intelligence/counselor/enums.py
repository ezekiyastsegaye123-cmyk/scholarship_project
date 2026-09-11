"""Bounded qualitative enums for the Scholarship Counselor Module.

Guarantees:
- Zero numerical scores (no fit_score, match_score, competitiveness_score, trust_score).
- Explicit qualitative classifications with formal definitions.
- Qualitative labels are decision-support aids, NOT probability estimates.
"""
from enum import Enum


from scholarship_intelligence.domain.enums import (
    AlignmentLevel,
    DeadlineReadiness,
    ReadinessLevel,
)

__all__ = [
    "AlignmentLevel",
    "ReadinessLevel",
    "DeadlineReadiness",
]
