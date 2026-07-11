"""
Pydantic schemas defining the data contracts between agents.

Every agent produces one of these models, ensuring type safety
and structured handoff through the LangGraph state machine.
"""

from typing import Literal
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    source: str
    excerpt: str
    relevance: str


class EvidenceReport(BaseModel):
    task_id: str
    scenario_summary: str
    similar_incidents: list[SourceReference]
    relevant_requirements: list[SourceReference]
    evidence_gaps: list[str]


class Hypothesis(BaseModel):
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_sources: list[str]


class AgentOpinion(BaseModel):
    agent_name: str
    key_findings: list[str]
    claims: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str]
    open_questions: list[str]


class ComparativeReview(BaseModel):
    agreements: list[str]
    disagreements: list[dict]
    weak_claims: list[str]
    unsupported_claims: list[str]
    additional_evidence_needed: list[str]
    synthesis_guidance: list[str]


class FinalSynthesis(BaseModel):
    final_summary: str
    accepted_findings: list[str]
    rejected_findings: list[str]
    unresolved_points: list[str]
    recommended_next_steps: list[str]


class ValidationIssue(BaseModel):
    severity: Literal["info", "warning", "critical"]
    description: str
    recommendation: str


class ValidationReport(BaseModel):
    passed: bool
    issues: list[ValidationIssue]
    supported_claims: int
    unsupported_claims: int


class ProposedAction(BaseModel):
    action_type: Literal["create_ticket", "save_report"]
    parameters: dict
    risk_level: Literal["low", "medium", "high"]


class AutomationResult(BaseModel):
    success: bool
    action_type: str
    output_reference: str | None = None
    error: str | None = None
