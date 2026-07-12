"""
LangGraph state machine for the investigation pipeline.

Flow:
  gather_evidence
    → [parallel] technical, quality, compliance
      → critic
        → synthesis
          → validation
            → (conditional) prepare_human_review or retry
              → human_approval
                → (conditional) automation or rejection
"""

from langgraph.graph import StateGraph, END

import config
from orchestrator.state import InvestigationState
from orchestrator.nodes import (
    gather_evidence,
    run_technical,
    run_quality,
    run_compliance,
    run_critic,
    run_synthesis,
    run_validation,
    prepare_human_review,
    human_approval,
    run_automation,
    handle_rejection,
)
from orchestrator.routing import route_after_validation, route_after_human


def build_graph() -> StateGraph:
    """
    Construct and compile the investigation graph.

    Returns a compiled LangGraph ready to .invoke().

    Whether the 3 specialist agents (Technical/Quality/Compliance) run
    concurrently or sequentially is controlled by config.PARALLEL_SPECIALISTS:
      - True  (default when LLM_BACKEND=vllm): all 3 fan out from
        gather_evidence and run concurrently. Safe because vLLM handles
        real concurrent requests via continuous batching.
      - False (default when LLM_BACKEND=ollama): the 3 run one after another
        in a chain. Local Ollama serves one request at a time by default and
        can drop connections under concurrent load, so sequential execution
        is the reliable default there.
    """
    graph = StateGraph(InvestigationState)

    # ── Add nodes ──
    graph.add_node("gather_evidence", gather_evidence)
    graph.add_node("run_technical", run_technical)
    graph.add_node("run_quality", run_quality)
    graph.add_node("run_compliance", run_compliance)
    graph.add_node("run_critic", run_critic)
    graph.add_node("run_synthesis", run_synthesis)
    graph.add_node("run_validation", run_validation)
    graph.add_node("prepare_human_review", prepare_human_review)
    graph.add_node("human_approval", human_approval)
    graph.add_node("run_automation", run_automation)
    graph.add_node("handle_rejection", handle_rejection)

    # ── Entry point ──
    graph.set_entry_point("gather_evidence")

    if config.PARALLEL_SPECIALISTS:
        # ── Concurrent: evidence → all 3 specialists fan out ──
        graph.add_edge("gather_evidence", "run_technical")
        graph.add_edge("gather_evidence", "run_quality")
        graph.add_edge("gather_evidence", "run_compliance")

        # ── All specialists → critic ──
        graph.add_edge("run_technical", "run_critic")
        graph.add_edge("run_quality", "run_critic")
        graph.add_edge("run_compliance", "run_critic")
    else:
        # ── Sequential: evidence → technical → quality → compliance → critic ──
        # Avoids sending concurrent requests to a single-request-at-a-time
        # local Ollama server.
        graph.add_edge("gather_evidence", "run_technical")
        graph.add_edge("run_technical", "run_quality")
        graph.add_edge("run_quality", "run_compliance")
        graph.add_edge("run_compliance", "run_critic")

    # ── Critic → synthesis → validation ──
    graph.add_edge("run_critic", "run_synthesis")
    graph.add_edge("run_synthesis", "run_validation")

    # ── Conditional: validation → human review or retry ──
    graph.add_conditional_edges(
        "run_validation",
        route_after_validation,
        {
            "prepare_human_review": "prepare_human_review",
            "run_synthesis": "run_synthesis",
        },
    )

    # ── Human review → approval ──
    graph.add_edge("prepare_human_review", "human_approval")

    # ── Conditional: approve → automation, reject → rejection ──
    graph.add_conditional_edges(
        "human_approval",
        route_after_human,
        {
            "run_automation": "run_automation",
            "handle_rejection": "handle_rejection",
        },
    )

    # ── Terminal nodes ──
    graph.add_edge("run_automation", END)
    graph.add_edge("handle_rejection", END)

    return graph.compile()
