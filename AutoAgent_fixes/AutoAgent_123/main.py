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
import sys
from datetime import datetime

from core.llm import LLM
from core.logger import log_event
from rag.setup import build_knowledge_adapter
from orchestrator.context import PipelineContext
from orchestrator.graph import build_graph


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

    print("=" * 60)
    print("  AutoAgent — Automotive Investigation Copilot")
    print("=" * 60)

    # ── Step 1: Build the RAG pipeline ──
    print("\n[INIT] Setting up RAG pipeline ...")
    adapter = build_knowledge_adapter(force_reingest=args.ingest)

    # ── Step 2: Initialize LLM ──
    print("[INIT] Connecting to Ollama LLM ...")
    llm = LLM(model=args.model)
    print(f"  Using model: {llm.model}")

    # ── Step 3: Build dependency context (thread-safe, no globals) ──
    ctx = PipelineContext(llm=llm, adapter=adapter)

    # ── Step 4: Build the LangGraph ──
    print("[INIT] Building investigation graph ...")
    graph = build_graph()

    # ── Step 5: Prepare initial state ──
    task_id = args.task_id or f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    user_request = args.query or DEMO_REQUEST

    initial_state = {
        "task_id": task_id,
        "user_request": user_request,
        "retry_count": 0,
    }

    log_event("investigation_start", "orchestrator", task_id, data={"request": user_request})

    print(f"\n[RUN] Starting investigation: {task_id}")
    print(f"  Request: {user_request[:80]}...")
    print()

    # ── Step 6: Run the graph ──
    try:
        final_state = graph.invoke(
            initial_state,
            config={"configurable": {"pipeline_ctx": ctx}},
        )
    except KeyboardInterrupt:
        print("\n\n[ABORT] Investigation cancelled by user.")
        log_event("investigation_aborted", "orchestrator", task_id)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Investigation failed: {e}")
        log_event("investigation_error", "orchestrator", task_id, data={"error": str(e)}, status="error")
        raise

    # ── Step 7: Summary ──
    print("\n" + "=" * 60)
    print("  INVESTIGATION COMPLETE")
    print("=" * 60)

    decision = final_state.get("human_decision", "unknown")
    print(f"  Decision: {decision}")

    if decision == "approve":
        for result in final_state.get("automation_results", []):
            status = "✓" if result.get("success") else "✗"
            print(f"  {status} {result.get('action_type')}: {result.get('output_reference', result.get('error'))}")

    log_event("investigation_complete", "orchestrator", task_id, data={"decision": decision})
    print(f"\n  Audit log: audit/events.jsonl")
    print()


if __name__ == "__main__":
    main()
