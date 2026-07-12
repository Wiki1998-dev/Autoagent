#!/usr/bin/env python3
"""
AutoAgent — Local Multi-Agent Engineering Copilot
for Automotive Failure Investigation.

Usage:
    python main.py                          # run the demo investigation
    python main.py --ingest                 # force re-ingest data into ChromaDB
    python main.py --query "your question"  # custom investigation request
"""

import argparse
import signal
import sys
from datetime import datetime

import structlog

from core.llm import LLM
from core.logger import log_event
from rag.setup import build_knowledge_adapter
from orchestrator.context import PipelineContext
from orchestrator.graph import build_graph

logger = structlog.get_logger("autoagent.main")


def _install_sigterm_handler(task_id: str) -> None:
    """Issue #21 — flush audit log and exit cleanly on SIGTERM (K8s, systemd)."""
    def _handler(signum, frame):  # noqa: ANN001
        logger.warning("sigterm_received", task_id=task_id)
        log_event("investigation_aborted", "orchestrator", task_id,
                  data={"signal": "SIGTERM"}, status="error")
        sys.exit(130)
    signal.signal(signal.SIGTERM, _handler)



DEMO_REQUEST = (
    "Investigate scenario SC-042, find similar incidents, analyze likely causes, "
    "compare technical, quality, and compliance perspectives, produce a critical "
    "synthesis, validate the conclusions, and create a follow-up engineering "
    "ticket after approval."
)


def main():
    parser = argparse.ArgumentParser(description="AutoAgent Investigation Pipeline")
    parser.add_argument("--ingest", action="store_true", help="Force re-ingest documents")
    parser.add_argument("--query", type=str, default=None, help="Custom investigation request")
    parser.add_argument("--model", type=str, default=None, help="Override LLM model name")
    parser.add_argument("--task-id", type=str, default=None, help="Investigation task ID (default: auto-generated)")
    args = parser.parse_args()

    # ── Step 5 first pass: generate task_id so SIGTERM handler has it ──
    task_id = args.task_id or f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    _install_sigterm_handler(task_id)

    logger.info("pipeline_init", phase="rag_setup")
    adapter = build_knowledge_adapter(force_reingest=args.ingest)

    logger.info("pipeline_init", phase="llm_connect")
    llm = LLM(model=args.model)
    logger.info("llm_ready", model=llm.model)

    ctx = PipelineContext(llm=llm, adapter=adapter)

    logger.info("pipeline_init", phase="build_graph")
    graph = build_graph()

    user_request = args.query or DEMO_REQUEST

    initial_state = {
        "task_id": task_id,
        "user_request": user_request,
        "retry_count": 0,
    }

    log_event("investigation_start", "orchestrator", task_id, data={"request": user_request})
    logger.info("investigation_start", task_id=task_id, request_preview=user_request[:80])

    # ── Run the graph ──
    try:
        final_state = graph.invoke(
            initial_state,
            config={"configurable": {"pipeline_ctx": ctx}},
        )
    except KeyboardInterrupt:
        logger.warning("investigation_aborted", task_id=task_id, reason="KeyboardInterrupt")
        log_event("investigation_aborted", "orchestrator", task_id)
        sys.exit(1)
    except Exception as e:
        logger.error("investigation_failed", task_id=task_id, error=str(e))
        log_event("investigation_error", "orchestrator", task_id, data={"error": str(e)}, status="error")
        raise

    decision = final_state.get("human_decision", "unknown")
    logger.info("investigation_complete", task_id=task_id, decision=decision)

    if decision == "approve":
        for result in final_state.get("automation_results", []):
            status = "ok" if result.get("success") else "error"
            logger.info("automation_result", action=result.get("action_type"),
                        status=status, ref=result.get("output_reference", result.get("error")))

    log_event("investigation_complete", "orchestrator", task_id, data={"decision": decision})


if __name__ == "__main__":
    main()

