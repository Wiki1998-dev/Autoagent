"""
Automation Agent — thin wrapper over the automation MCP server tools.

All file-writing logic lives in mcp_servers/automation_server.py.
This class exists only to keep the agent API consistent with the rest
of the pipeline and to log audit events.
"""

from core.schemas import AutomationResult
from core.logger import log_event
from mcp_servers.automation_server import save_report as _save_report
from mcp_servers.automation_server import create_ticket as _create_ticket


class AutomationAgent:
    def run(
        self,
        task_id: str,
        final_synthesis: dict,
        report_markdown: str,
        human_feedback: str = "",
    ) -> list[AutomationResult]:
        """Execute approved automation actions via the MCP server tools."""
        log_event("agent_start", "automation_agent", task_id)
        results: list[AutomationResult] = []

        # ── Action 1: Save investigation report ──
        try:
            r = _save_report(task_id=task_id, report_markdown=report_markdown)
            results.append(
                AutomationResult(
                    success=r.success,
                    action_type="save_report",
                    output_reference=r.path,
                )
            )
            log_event("action_executed", "automation_agent", task_id,
                      data={"action": "save_report", "path": r.path})
        except Exception as e:
            results.append(AutomationResult(success=False, action_type="save_report", error=str(e)))

        # ── Action 2: Create follow-up ticket ──
        try:
            r = _create_ticket(
                title=f"Follow-up: Investigation {task_id}",
                body=final_synthesis.get("final_summary", "See attached report."),
                metadata={
                    "task_id": task_id,
                    "next_steps": final_synthesis.get("recommended_next_steps", []),
                    "human_feedback": human_feedback,
                },
            )
            results.append(
                AutomationResult(
                    success=r.success,
                    action_type="create_ticket",
                    output_reference=r.ticket_id,
                )
            )
            log_event("action_executed", "automation_agent", task_id,
                      data={"action": "create_ticket", "ticket_id": r.ticket_id})
        except Exception as e:
            results.append(AutomationResult(success=False, action_type="create_ticket", error=str(e)))

        log_event("agent_complete", "automation_agent", task_id, data={"actions": len(results)})
        return results

