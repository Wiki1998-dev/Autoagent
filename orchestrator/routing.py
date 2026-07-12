"""
Routing functions for conditional edges in the LangGraph.
"""

import structlog

from orchestrator.state import InvestigationState

logger = structlog.get_logger("autoagent.routing")



def route_after_validation(state: InvestigationState) -> str:
    """
    After validation, decide whether to proceed to human review
    or loop back for retry (max 2 retries).
    """
    validation = state.get("validation_report", {})
    retry_count = state.get("retry_count", 0)

    # If validation passed, proceed to human review
    if validation.get("passed", False):
        return "prepare_human_review"

    # retry_count is incremented by run_synthesis before this check fires.
    # After attempt 1 → retry_count=1, after attempt 2 → retry_count=2.
    # Allow a third pass (retry_count=2 entering synthesis → 3 exiting) so
    # the system gets exactly MAX_SYNTHESIS_RETRIES=2 genuine retries.
    MAX_RETRIES = 2
    if retry_count > MAX_RETRIES:
        logger.warning("max_retries_exceeded", retry_count=retry_count)
        return "prepare_human_review"

    # Otherwise retry synthesis
    logger.info("retrying_synthesis", attempt=retry_count + 1)
    return "run_synthesis"


def route_after_human(state: InvestigationState) -> str:
    """Route based on human approval decision."""
    decision = state.get("human_decision", "reject")

    if decision == "approve":
        return "run_automation"
    else:
        return "handle_rejection"
