"""Strict student profile field registry and safe value resolver.

Security Guarantees:
- Strict allowlist of permitted profile fields (no arbitrary getattr or traversal).
- Rejects unknown or forbidden attributes.
- Handles conflicting student data deterministically.
- Distinguishes missing data (None -> UNKNOWN) from defined values.
"""
from dataclasses import dataclass
from typing import Any, Optional, Set
from scholarship_intelligence.domain.enums import RuleComparisonOp


@dataclass(frozen=True)
class FieldMetadata:
    canonical_name: str
    data_type: str  # "string", "float", "int", "list", "enum"
    supported_ops: Set[RuleComparisonOp]
    description: str


# Canonical field definitions
REGISTERED_FIELDS: dict[str, FieldMetadata] = {
    "citizenship_country": FieldMetadata(
        canonical_name="citizenship_country",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Student citizenship country ISO code or name",
    ),
    "residence_country": FieldMetadata(
        canonical_name="residence_country",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Student country of permanent residence",
    ),
    "intended_degree_level": FieldMetadata(
        canonical_name="intended_degree_level",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Intended degree level (strictly BACHELOR for MVP)",
    ),
    "intended_destination_country": FieldMetadata(
        canonical_name="intended_destination_country",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Intended study destination country (strictly US for MVP)",
    ),
    "gpa": FieldMetadata(
        canonical_name="gpa",
        data_type="float",
        supported_ops={
            RuleComparisonOp.EQ, RuleComparisonOp.NEQ,
            RuleComparisonOp.GT, RuleComparisonOp.GTE,
            RuleComparisonOp.LT, RuleComparisonOp.LTE,
        },
        description="Grade point average (scale-aware)",
    ),
    "gpa_scale": FieldMetadata(
        canonical_name="gpa_scale",
        data_type="float",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ},
        description="Grading scale basis for GPA (e.g. 4.0)",
    ),
    "intended_major": FieldMetadata(
        canonical_name="intended_major",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN, RuleComparisonOp.CONTAINS},
        description="Intended major or academic field of study",
    ),
    "english_test_type": FieldMetadata(
        canonical_name="english_test_type",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Type of standardized English proficiency exam (e.g. TOEFL, IELTS)",
    ),
    "english_test_score": FieldMetadata(
        canonical_name="english_test_score",
        data_type="float",
        supported_ops={
            RuleComparisonOp.EQ, RuleComparisonOp.NEQ,
            RuleComparisonOp.GT, RuleComparisonOp.GTE,
            RuleComparisonOp.LT, RuleComparisonOp.LTE,
        },
        description="Numeric score on English proficiency exam",
    ),
    "sat_score": FieldMetadata(
        canonical_name="sat_score",
        data_type="int",
        supported_ops={
            RuleComparisonOp.EQ, RuleComparisonOp.NEQ,
            RuleComparisonOp.GT, RuleComparisonOp.GTE,
            RuleComparisonOp.LT, RuleComparisonOp.LTE,
        },
        description="SAT total score (400 - 1600)",
    ),
    "act_score": FieldMetadata(
        canonical_name="act_score",
        data_type="int",
        supported_ops={
            RuleComparisonOp.EQ, RuleComparisonOp.NEQ,
            RuleComparisonOp.GT, RuleComparisonOp.GTE,
            RuleComparisonOp.LT, RuleComparisonOp.LTE,
        },
        description="ACT composite score (1 - 36)",
    ),
    "financial_need_tier": FieldMetadata(
        canonical_name="financial_need_tier",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Broad financial need level tier (HIGH, MODERATE, LOW, NONE)",
    ),
    "academic_achievements": FieldMetadata(
        canonical_name="academic_achievements",
        data_type="list",
        supported_ops={RuleComparisonOp.CONTAINS},
        description="List of academic honors and achievements",
    ),
    "extracurricular_activities": FieldMetadata(
        canonical_name="extracurricular_activities",
        data_type="list",
        supported_ops={RuleComparisonOp.CONTAINS},
        description="List of student extracurricular activities",
    ),
    "interests": FieldMetadata(
        canonical_name="interests",
        data_type="list",
        supported_ops={RuleComparisonOp.CONTAINS},
        description="List of academic or personal interests",
    ),
    "class_rank": FieldMetadata(
        canonical_name="class_rank",
        data_type="string",
        supported_ops={RuleComparisonOp.EQ, RuleComparisonOp.NEQ, RuleComparisonOp.IN},
        description="Relative academic standing or class rank tier",
    ),
}

# Aliases mapping alternative domain rule field names to canonical fields
FIELD_ALIASES: dict[str, str] = {
    "nationality": "citizenship_country",
    "citizenship": "citizenship_country",
    "country_of_citizenship": "citizenship_country",
    "country_of_residence": "residence_country",
    "residence": "residence_country",
    "degree_level": "intended_degree_level",
    "destination_country": "intended_destination_country",
    "major": "intended_major",
    "sat": "sat_score",
    "act": "act_score",
    "toefl": "english_test_score",
    "toefl_score": "english_test_score",
    "ielts": "english_test_score",
    "ielts_score": "english_test_score",
    "english_score": "english_test_score",
}


def resolve_field_name(raw_field: str) -> Optional[str]:
    """Resolves a raw field name or alias to its canonical name if in allowlist."""
    norm = raw_field.strip().lower()
    if norm in REGISTERED_FIELDS:
        return norm
    if norm in FIELD_ALIASES:
        return FIELD_ALIASES[norm]
    return None


def is_field_allowed(raw_field: str) -> bool:
    """Checks if a field name is in the strict allowlist."""
    return resolve_field_name(raw_field) is not None


def get_field_metadata(raw_field: str) -> Optional[FieldMetadata]:
    """Retrieves metadata for a registered field."""
    canon = resolve_field_name(raw_field)
    if canon is None:
        return None
    return REGISTERED_FIELDS[canon]


def extract_student_value(
    student_profile: Any,
    raw_field: str,
) -> tuple[Optional[Any], bool, Optional[float]]:
    """Safely extracts value from student profile.
    
    Returns:
        (value, is_conflicting, student_gpa_scale)
    """
    canonical_name = resolve_field_name(raw_field)
    if not canonical_name:
        return None, False, None
    
    # 1. Check for conflicting fields flag on profile
    conflicted_fields: set[str] = set()
    if isinstance(student_profile, dict):
        conflicted_fields = set(student_profile.get("_conflicts", [])) | set(student_profile.get("conflicted_fields", []))
    else:
        conflicted_fields = getattr(student_profile, "conflicted_fields", set()) or set()
    
    # Normalize conflicted field names
    norm_conflicts = {resolve_field_name(f) for f in conflicted_fields if resolve_field_name(f)}
    if canonical_name in norm_conflicts:
        return None, True, None
    
    # 2. Extract value from dict or object safely
    value: Any = None
    if isinstance(student_profile, dict):
        value = student_profile.get(canonical_name)
        # Check alias in dict if canonical not set
        if value is None and raw_field in student_profile:
            value = student_profile[raw_field]
    else:
        value = getattr(student_profile, canonical_name, None)
        if value is None and hasattr(student_profile, raw_field):
            value = getattr(student_profile, raw_field, None)
    
    # 3. Detect implicit conflicting data (e.g. if field value itself is a set/list with conflicting values for a scalar field)
    meta = REGISTERED_FIELDS[canonical_name]
    if meta.data_type in ("string", "float", "int") and isinstance(value, (list, set, tuple)):
        # If scalar field contains multiple distinct values, it's conflicting
        if len(set(value)) > 1:
            return None, True, None
        elif len(value) == 1:
            value = next(iter(value))
        else:
            value = None

    # 4. Extract scale if gpa
    student_scale: Optional[float] = None
    if canonical_name == "gpa":
        if isinstance(student_profile, dict):
            student_scale = student_profile.get("gpa_scale", 4.0)
        else:
            student_scale = getattr(student_profile, "gpa_scale", 4.0)
    
    return value, False, student_scale
