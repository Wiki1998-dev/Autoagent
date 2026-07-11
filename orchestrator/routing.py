"""
Routing functions for conditional edges in the LangGraph.
"""

from orchestrator.state import InvestigationState


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

    # If too many retries, proceed anyway with warnings
    if retry_count >= 2:
        print(f"  ⚠ Validation failed after {retry_count} retries, proceeding with warnings")
        return "prepare_human_review"

    # Otherwise retry synthesis
    print(f"  ↻ Validation failed, retrying synthesis (attempt {retry_count + 1})")
    return "run_synthesis"


def route_after_human(state: InvestigationState) -> str:
    """Route based on human approval decision."""
    decision = state.get("human_decision", "reject")

    if decision == "approve":
        return "run_automation"
    else:
        return "handle_rejection"
