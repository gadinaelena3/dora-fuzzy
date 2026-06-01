"""Pydantic schemas for request/response validation."""
from typing import Dict, List
from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    """Single-project assessment input."""
    dspd: float = Field(..., ge=0, le=50, description="Delivered Story Points per Deployment")
    ltbf: float = Field(..., ge=0, le=30, description="Lead Time for Business Features (days)")
    qd:   float = Field(..., ge=0, le=10, description="Quality Duo (Acceptance Rate / Code Churn)")
    project_name: str | None = Field(default=None, description="Optional label for reporting")


class RuleActivation(BaseModel):
    id: str
    antecedents: Dict[str, str]
    consequent: str
    firing_strength: float
    rationale: str


class AssessmentResponse(BaseModel):
    project_name: str | None
    inputs: Dict[str, float]
    phs: float
    linguistic_state: str
    state_membership: float
    input_memberships: Dict[str, Dict[str, float]]
    rule_activations: List[RuleActivation]


class BatchResponse(BaseModel):
    """Batch assessment over a CSV upload."""
    n_projects: int
    results: List[AssessmentResponse]
    summary: Dict[str, int]   # counts by linguistic state


class MembershipCurves(BaseModel):
    """All MF curves for plotting in the UI."""
    DSPD: Dict
    LTBF: Dict
    Qd:   Dict
    PHS:  Dict
