"""Pydantic schemas for eligibility rules and general opportunity requirements."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

from scholarship_intelligence.domain.enums import RequirementKind, RequirementType, RuleKind
from scholarship_intelligence.domain.rules import RuleExpression


class EligibilityRuleBase(BaseModel):
    rule_id: str = Field(..., min_length=1, max_length=100)
    kind: RuleKind = Field(default=RuleKind.REQUIRED)
    expression: RuleExpression
    description: Optional[str] = None
    source_evidence_snippet: Optional[str] = None
    is_verified: bool = False


class EligibilityRuleCreate(EligibilityRuleBase):
    pass


class EligibilityRuleRead(EligibilityRuleBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)


class RequirementBase(BaseModel):
    requirement_type: RequirementType
    kind: RequirementKind = Field(default=RequirementKind.REQUIRED)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    source_evidence_snippet: Optional[str] = None


class RequirementCreate(RequirementBase):
    pass


class RequirementRead(RequirementBase):
    id: str
    scholarship_id: str
    model_config = ConfigDict(from_attributes=True)
