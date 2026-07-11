"""
LangGraph state definition for the investigation pipeline.

This TypedDict flows through every node in the graph.
Each agent writes its output into the appropriate key.
"""

from typing import TypedDict


class InvestigationState(TypedDict, total=False):
    # ── Input ──
    task_id: str
    user_request: str

    # ── Evidence Agent output ──
    evidence_report: dict

    # ── Specialist Agent outputs (run in parallel) ──
    technical_opinion: dict
    quality_opinion: dict
    compliance_opinion: dict

    # ── Critic Agent output ──
    comparative_review: dict

    # ── Synthesis Agent output ──
    final_synthesis: dict

    # ── Validator Agent output ──
    validation_report: dict

    # ── Report for human review ──
    report_markdown: str

    # ── Proposed actions ──
    proposed_actions: list[dict]

    # ── Human decision ──
    human_decision: str  # "approve" or "reject"
    human_feedback: str

    # ── Automation Agent output ──
    automation_results: list[dict]

    # ── Retry tracking ──
    retry_count: int
