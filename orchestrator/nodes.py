"""
LangGraph node functions.

Each function:
  1. Takes InvestigationState
  2. Runs one agent
  3. Returns a dict of state updates

The graph wires these together.
"""

import json
from datetime import datetime

from orchestrator.state import InvestigationState
from agents.evidence_agent import EvidenceAgent
from agents.technical_agent import TechnicalAgent
from agents.quality_agent import QualityAgent
from agents.compliance_agent import ComplianceAgent
from agents.critic_agent import CriticAgent
from agents.synthesis_agent import SynthesisAgent
from agents.validator_agent import ValidatorAgent
from agents.automation_agent import AutomationAgent

from mcp_servers.analysis_server import get_scenario_metadata
from core.llm import LLM
from core.logger import log_event
from rag.adapter import KnowledgeAdapter


# ── Module-level references (injected at startup) ──
_llm: LLM | None = None
_adapter: KnowledgeAdapter | None = None


def init_nodes(llm: LLM, adapter: KnowledgeAdapter):
    """Called once at startup to inject dependencies."""
    global _llm, _adapter
    _llm = llm
    _adapter = adapter


# ──────────────────────────────────────────────────────────────
# Node: gather_evidence
# ──────────────────────────────────────────────────────────────
def gather_evidence(state: InvestigationState) -> dict:
    """Runs the Evidence Agent."""
    task_id = state["task_id"]
    print(f"\n{'='*60}")
    print(f"[1/8] Evidence Agent — gathering evidence for {task_id}")
    print(f"{'='*60}")

    # Get scenario metadata from analysis server
    scenario_id = task_id  # SC-042
    scenario_data = get_scenario_metadata(scenario_id)

    agent = EvidenceAgent(llm=_llm, adapter=_adapter)
    report = agent.run(
        task_id=task_id,
        user_request=state["user_request"],
        scenario_data=scenario_data,
    )

    print(f"  → Found {len(report.similar_incidents)} incidents, "
          f"{len(report.relevant_requirements)} requirements, "
          f"{len(report.evidence_gaps)} gaps")

    return {"evidence_report": report.model_dump()}


# ──────────────────────────────────────────────────────────────
# Nodes: specialist agents (can run in parallel)
# ──────────────────────────────────────────────────────────────
def run_technical(state: InvestigationState) -> dict:
    """Runs the Technical Analysis Agent."""
    print(f"\n[2a/8] Technical Agent — analyzing ...")
    agent = TechnicalAgent(llm=_llm)
    opinion = agent.run(state["task_id"], state["evidence_report"])
    print(f"  → confidence={opinion.confidence}, findings={len(opinion.key_findings)}")
    return {"technical_opinion": opinion.model_dump()}


def run_quality(state: InvestigationState) -> dict:
    """Runs the Quality/Risk Agent."""
    print(f"\n[2b/8] Quality Agent — assessing risk ...")
    agent = QualityAgent(llm=_llm)
    opinion = agent.run(state["task_id"], state["evidence_report"])
    print(f"  → confidence={opinion.confidence}, findings={len(opinion.key_findings)}")
    return {"quality_opinion": opinion.model_dump()}


def run_compliance(state: InvestigationState) -> dict:
    """Runs the Compliance Agent."""
    print(f"\n[2c/8] Compliance Agent — checking requirements ...")
    agent = ComplianceAgent(llm=_llm)
    opinion = agent.run(state["task_id"], state["evidence_report"])
    print(f"  → confidence={opinion.confidence}, findings={len(opinion.key_findings)}")
    return {"compliance_opinion": opinion.model_dump()}


# ──────────────────────────────────────────────────────────────
# Node: critic
# ──────────────────────────────────────────────────────────────
def run_critic(state: InvestigationState) -> dict:
    """Runs the Critic Agent to compare specialist opinions."""
    print(f"\n[3/8] Critic Agent — comparing opinions ...")
    agent = CriticAgent(llm=_llm)
    review = agent.run(
        task_id=state["task_id"],
        technical_opinion=state["technical_opinion"],
        quality_opinion=state["quality_opinion"],
        compliance_opinion=state["compliance_opinion"],
    )
    print(f"  → {len(review.agreements)} agreements, "
          f"{len(review.disagreements)} disagreements, "
          f"{len(review.weak_claims)} weak claims")
    return {"comparative_review": review.model_dump()}


# ──────────────────────────────────────────────────────────────
# Node: synthesis
# ──────────────────────────────────────────────────────────────
def run_synthesis(state: InvestigationState) -> dict:
    """Runs the Synthesis Agent to produce the final summary."""
    print(f"\n[4/8] Synthesis Agent — producing final summary ...")
    agent = SynthesisAgent(llm=_llm)
    synthesis = agent.run(
        task_id=state["task_id"],
        evidence_report=state["evidence_report"],
        technical_opinion=state["technical_opinion"],
        quality_opinion=state["quality_opinion"],
        compliance_opinion=state["compliance_opinion"],
        comparative_review=state["comparative_review"],
    )
    print(f"  → accepted={len(synthesis.accepted_findings)}, "
          f"rejected={len(synthesis.rejected_findings)}")
    return {"final_synthesis": synthesis.model_dump()}


# ──────────────────────────────────────────────────────────────
# Node: validation
# ──────────────────────────────────────────────────────────────
def run_validation(state: InvestigationState) -> dict:
    """Runs the Validator Agent to quality-check the synthesis."""
    print(f"\n[5/8] Validator Agent — checking synthesis quality ...")
    agent = ValidatorAgent(llm=_llm)
    report = agent.run(
        task_id=state["task_id"],
        evidence_report=state["evidence_report"],
        final_synthesis=state["final_synthesis"],
        comparative_review=state["comparative_review"],
    )
    print(f"  → passed={report.passed}, supported={report.supported_claims}, "
          f"unsupported={report.unsupported_claims}")
    return {"validation_report": report.model_dump()}


# ──────────────────────────────────────────────────────────────
# Node: prepare for human review
# ──────────────────────────────────────────────────────────────
def prepare_human_review(state: InvestigationState) -> dict:
    """Formats the results for human review."""
    print(f"\n[6/8] Preparing human review package ...")
    synthesis = state["final_synthesis"]
    validation = state["validation_report"]

    report_lines = [
        f"# Investigation Report: {state['task_id']}",
        f"Date: {datetime.now().isoformat()}",
        "",
        "## Final Summary",
        synthesis.get("final_summary", "N/A"),
        "",
        "## Accepted Findings",
    ]
    for f in synthesis.get("accepted_findings", []):
        report_lines.append(f"- {f}")

    report_lines += ["", "## Rejected Findings"]
    for f in synthesis.get("rejected_findings", []):
        report_lines.append(f"- {f}")

    report_lines += ["", "## Unresolved Points"]
    for p in synthesis.get("unresolved_points", []):
        report_lines.append(f"- {p}")

    report_lines += ["", "## Recommended Next Steps"]
    for s in synthesis.get("recommended_next_steps", []):
        report_lines.append(f"- {s}")

    report_lines += [
        "",
        "## Validation",
        f"Passed: {validation.get('passed')}",
        f"Supported claims: {validation.get('supported_claims')}",
        f"Unsupported claims: {validation.get('unsupported_claims')}",
    ]

    for issue in validation.get("issues", []):
        report_lines.append(f"- [{issue.get('severity', 'info')}] {issue.get('description', '')}")

    report_md = "\n".join(report_lines)

    proposed = [
        {"action_type": "save_report", "parameters": {"task_id": state["task_id"]}, "risk_level": "low"},
        {"action_type": "create_ticket", "parameters": {"task_id": state["task_id"]}, "risk_level": "medium"},
    ]

    print(f"  → Report ready ({len(report_md)} chars), {len(proposed)} proposed actions")

    return {
        "report_markdown": report_md,
        "proposed_actions": proposed,
    }


# ──────────────────────────────────────────────────────────────
# Node: human approval (waits for input)
# ──────────────────────────────────────────────────────────────
def human_approval(state: InvestigationState) -> dict:
    """
    Pauses for human review and approval.
    In a real deployment this would be a Streamlit form or API callback.
    For CLI demo, uses input().
    """
    print(f"\n{'='*60}")
    print("[7/8] HUMAN APPROVAL REQUIRED")
    print(f"{'='*60}")
    print()
    print(state.get("report_markdown", "(no report)"))
    print()
    print("Proposed actions:")
    for action in state.get("proposed_actions", []):
        print(f"  - {action['action_type']} (risk: {action['risk_level']})")
    print()

    decision = input("Approve these actions? (approve/reject): ").strip().lower()
    feedback = ""
    if decision == "reject":
        feedback = input("Feedback (why rejected): ").strip()

    log_event(
        "human_decision",
        "human",
        state["task_id"],
        data={"decision": decision, "feedback": feedback},
    )

    return {"human_decision": decision, "human_feedback": feedback}


# ──────────────────────────────────────────────────────────────
# Node: automation
# ──────────────────────────────────────────────────────────────
def run_automation(state: InvestigationState) -> dict:
    """Executes approved automation actions."""
    print(f"\n[8/8] Automation Agent — executing approved actions ...")
    agent = AutomationAgent()
    results = agent.run(
        task_id=state["task_id"],
        final_synthesis=state["final_synthesis"],
        human_feedback=state.get("human_feedback", ""),
    )

    for r in results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.action_type}: {r.output_reference or r.error}")

    return {"automation_results": [r.model_dump() for r in results]}


# ──────────────────────────────────────────────────────────────
# Node: rejected (when human says no)
# ──────────────────────────────────────────────────────────────
def handle_rejection(state: InvestigationState) -> dict:
    """Handles a rejected investigation."""
    print(f"\n[REJECTED] Human rejected the investigation output.")
    print(f"  Feedback: {state.get('human_feedback', 'none')}")
    log_event(
        "investigation_rejected",
        "orchestrator",
        state["task_id"],
        data={"feedback": state.get("human_feedback", "")},
    )
    return {}
