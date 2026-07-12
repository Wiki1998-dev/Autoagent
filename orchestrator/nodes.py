"""
LangGraph node functions.

Each function:
  1. Takes InvestigationState
  2. Runs one agent
  3. Returns a dict of state updates

The graph wires these together.

Architecture note on MCP (#1):
  Tools in mcp_servers/ are called via their module-level functions
  (same process, no HTTP hop) in the CLI workflow. In a distributed
  deployment each server would be spun up independently and called over
  the network via the FastMCP client. The boundary is the function
  signature — do NOT import agent internals from mcp_servers directly;
  only call the decorated @mcp.tool() functions.
"""

from datetime import datetime
import structlog

from orchestrator.state import InvestigationState
from agents.evidence_agent import EvidenceAgent
from agents.technical_agent import TechnicalAgent
from agents.quality_agent import QualityAgent
from agents.compliance_agent import ComplianceAgent
from agents.critic_agent import CriticAgent
from agents.synthesis_agent import SynthesisAgent
from agents.validator_agent import ValidatorAgent
from agents.automation_agent import AutomationAgent

# ── MCP tool boundary ─────────────────────────────────────────
# In-process call for CLI mode. Replace with FastMCP client calls
# when running servers as independent processes.
from mcp_servers.analysis_server import get_scenario_metadata as _mcp_get_scenario_metadata

from core.llm import LLMParseError
from core.logger import log_event
from langchain_core.runnables import RunnableConfig
from orchestrator.context import PipelineContext

logger = structlog.get_logger("autoagent.nodes")


def _ctx(config: RunnableConfig) -> PipelineContext:
    """Pull the PipelineContext injected via graph.invoke(config=...)."""
    ctx = config.get("configurable", {}).get("pipeline_ctx")
    if ctx is None:
        raise RuntimeError(
            "PipelineContext not found in graph config. "
            "Pass config={'configurable': {'pipeline_ctx': ctx}} to graph.invoke()."
        )
    return ctx


def _validate_state_entry(state: InvestigationState) -> None:
    """Issue #9 — validate required fields at graph boundary before any agent runs."""
    task_id = state.get("task_id", "")
    user_request = state.get("user_request", "")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("InvestigationState.task_id must be a non-empty string.")
    if not isinstance(user_request, str) or not user_request.strip():
        raise ValueError("InvestigationState.user_request must be a non-empty string.")


# ──────────────────────────────────────────────────────────────
# Node: gather_evidence
# ──────────────────────────────────────────────────────────────
def gather_evidence(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Evidence Agent."""
    _validate_state_entry(state)
    ctx = _ctx(config)
    task_id = state["task_id"]
    logger.info("node_start", node="gather_evidence", task_id=task_id)

    # ── Issue #1: call the MCP tool via its decorated boundary ──
    scenario_data = _mcp_get_scenario_metadata(scenario_id=task_id)
    if "error" in scenario_data:
        logger.warning(
            "scenario_load_failed",
            task_id=task_id,
            error=scenario_data["error"],
        )
        scenario_data = {}   # proceed with empty — evidence agent handles gaps

    # ── Issue #2/#6: guard against LLMParseError / ConnectionError ──
    try:
        agent = EvidenceAgent(llm=ctx.llm, adapter=ctx.adapter)
        report = agent.run(
            task_id=task_id,
            user_request=state["user_request"],
            scenario_data=scenario_data,
        )
        logger.info(
            "node_complete",
            node="gather_evidence",
            task_id=task_id,
            incidents=len(report.similar_incidents),
            requirements=len(report.relevant_requirements),
            gaps=len(report.evidence_gaps),
        )
        return {"evidence_report": report.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="gather_evidence", task_id=task_id, error=str(e))
        log_event("node_error", "gather_evidence", task_id, data={"error": str(e)}, status="error")
        # Return a minimal stub so downstream nodes can still run
        return {
            "evidence_report": {
                "task_id": task_id,
                "scenario_summary": f"Evidence collection failed: {e}",
                "similar_incidents": [],
                "relevant_requirements": [],
                "evidence_gaps": ["Evidence collection failed — LLM unavailable."],
            }
        }


# ──────────────────────────────────────────────────────────────
# Nodes: specialist agents (can run in parallel)
# ──────────────────────────────────────────────────────────────
def run_technical(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Technical Analysis Agent."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_technical", task_id=task_id)
    try:
        agent = TechnicalAgent(llm=_ctx(config).llm)
        opinion = agent.run(task_id, state["evidence_report"])
        logger.info("node_complete", node="run_technical", task_id=task_id,
                    confidence=opinion.confidence, findings=len(opinion.key_findings))
        return {"technical_opinion": opinion.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_technical", task_id=task_id, error=str(e))
        log_event("node_error", "run_technical", task_id, data={"error": str(e)}, status="error")
        return {"technical_opinion": {"agent_name": "technical_agent", "key_findings": [],
                "claims": [], "confidence": 0.0, "evidence_refs": [],
                "open_questions": [f"Agent failed: {e}"]}}


def run_quality(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Quality/Risk Agent."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_quality", task_id=task_id)
    try:
        agent = QualityAgent(llm=_ctx(config).llm)
        opinion = agent.run(task_id, state["evidence_report"])
        logger.info("node_complete", node="run_quality", task_id=task_id,
                    confidence=opinion.confidence, findings=len(opinion.key_findings))
        return {"quality_opinion": opinion.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_quality", task_id=task_id, error=str(e))
        log_event("node_error", "run_quality", task_id, data={"error": str(e)}, status="error")
        return {"quality_opinion": {"agent_name": "quality_agent", "key_findings": [],
                "claims": [], "confidence": 0.0, "evidence_refs": [],
                "open_questions": [f"Agent failed: {e}"]}}


def run_compliance(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Compliance Agent."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_compliance", task_id=task_id)
    try:
        agent = ComplianceAgent(llm=_ctx(config).llm)
        opinion = agent.run(task_id, state["evidence_report"])
        logger.info("node_complete", node="run_compliance", task_id=task_id,
                    confidence=opinion.confidence, findings=len(opinion.key_findings))
        return {"compliance_opinion": opinion.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_compliance", task_id=task_id, error=str(e))
        log_event("node_error", "run_compliance", task_id, data={"error": str(e)}, status="error")
        return {"compliance_opinion": {"agent_name": "compliance_agent", "key_findings": [],
                "claims": [], "confidence": 0.0, "evidence_refs": [],
                "open_questions": [f"Agent failed: {e}"]}}


# ──────────────────────────────────────────────────────────────
# Node: critic
# ──────────────────────────────────────────────────────────────
def run_critic(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Critic Agent to compare specialist opinions."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_critic", task_id=task_id)
    try:
        agent = CriticAgent(llm=_ctx(config).llm)
        review = agent.run(
            task_id=task_id,
            technical_opinion=state["technical_opinion"],
            quality_opinion=state["quality_opinion"],
            compliance_opinion=state["compliance_opinion"],
        )
        logger.info("node_complete", node="run_critic", task_id=task_id,
                    agreements=len(review.agreements),
                    disagreements=len(review.disagreements),
                    weak_claims=len(review.weak_claims))
        return {"comparative_review": review.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_critic", task_id=task_id, error=str(e))
        log_event("node_error", "run_critic", task_id, data={"error": str(e)}, status="error")
        return {"comparative_review": {"agreements": [], "disagreements": [],
                "weak_claims": [], "unsupported_claims": [],
                "additional_evidence_needed": [], "synthesis_guidance": []}}


# ──────────────────────────────────────────────────────────────
# Node: synthesis
# ──────────────────────────────────────────────────────────────
def run_synthesis(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Synthesis Agent to produce the final summary."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_synthesis", task_id=task_id)
    try:
        agent = SynthesisAgent(llm=_ctx(config).llm)
        synthesis = agent.run(
            task_id=task_id,
            evidence_report=state["evidence_report"],
            technical_opinion=state["technical_opinion"],
            quality_opinion=state["quality_opinion"],
            compliance_opinion=state["compliance_opinion"],
            comparative_review=state["comparative_review"],
        )
        logger.info("node_complete", node="run_synthesis", task_id=task_id,
                    accepted=len(synthesis.accepted_findings),
                    rejected=len(synthesis.rejected_findings))
        return {
            "final_synthesis": synthesis.model_dump(),
            "retry_count": state.get("retry_count", 0) + 1,
        }
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_synthesis", task_id=task_id, error=str(e))
        log_event("node_error", "run_synthesis", task_id, data={"error": str(e)}, status="error")
        return {
            "final_synthesis": {
                "final_summary": f"Synthesis failed: {e}",
                "accepted_findings": [],
                "rejected_findings": [],
                "unresolved_points": ["Synthesis agent failed — manual review required."],
                "recommended_next_steps": [],
            },
            "retry_count": state.get("retry_count", 0) + 1,
        }


# ──────────────────────────────────────────────────────────────
# Node: validation
# ──────────────────────────────────────────────────────────────
def run_validation(state: InvestigationState, config: RunnableConfig) -> dict:
    """Runs the Validator Agent to quality-check the synthesis."""
    task_id = state["task_id"]
    logger.info("node_start", node="run_validation", task_id=task_id)
    try:
        agent = ValidatorAgent(llm=_ctx(config).llm)
        report = agent.run(
            task_id=task_id,
            evidence_report=state["evidence_report"],
            final_synthesis=state["final_synthesis"],
            comparative_review=state["comparative_review"],
        )
        logger.info("node_complete", node="run_validation", task_id=task_id,
                    passed=report.passed,
                    supported=report.supported_claims,
                    unsupported=report.unsupported_claims)
        return {"validation_report": report.model_dump()}
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", node="run_validation", task_id=task_id, error=str(e))
        log_event("node_error", "run_validation", task_id, data={"error": str(e)}, status="error")
        # Treat a failed validator as a non-pass so the retry path fires (if retries left)
        return {"validation_report": {"passed": False, "issues": [], "supported_claims": 0,
                "unsupported_claims": 0}}


# ──────────────────────────────────────────────────────────────
# Node: prepare for human review
# ──────────────────────────────────────────────────────────────
def prepare_human_review(state: InvestigationState) -> dict:
    """Formats the results for human review."""
    logger.info("node_start", node="prepare_human_review", task_id=state["task_id"])
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

    logger.info("node_complete", node="prepare_human_review",
                task_id=state["task_id"], report_chars=len(report_md))

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
    task_id = state["task_id"]
    logger.info("node_start", node="run_automation", task_id=task_id)
    agent = AutomationAgent()
    results = agent.run(
        task_id=task_id,
        final_synthesis=state["final_synthesis"],
        report_markdown=state.get("report_markdown", ""),
        human_feedback=state.get("human_feedback", ""),
    )

    for r in results:
        status = "ok" if r.success else "error"
        logger.info("automation_action", task_id=task_id, action=r.action_type,
                    status=status, ref=r.output_reference or r.error)

    return {"automation_results": [r.model_dump() for r in results]}


# ──────────────────────────────────────────────────────────────
# Node: rejected (when human says no)
# ──────────────────────────────────────────────────────────────
def handle_rejection(state: InvestigationState) -> dict:
    """Handles a rejected investigation."""
    task_id = state["task_id"]
    feedback = state.get("human_feedback", "")
    logger.warning("investigation_rejected", task_id=task_id, feedback=feedback)
    log_event(
        "investigation_rejected",
        "orchestrator",
        task_id,
        data={"feedback": feedback},
    )
    return {}