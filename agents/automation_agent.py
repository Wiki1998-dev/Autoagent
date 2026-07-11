"""
Automation Agent.

Executes approved actions: saves the investigation report
and creates an engineering follow-up ticket.

Only runs after explicit human approval.
"""

import json
from datetime import datetime
from pathlib import Path

from core.schemas import AutomationResult
from core.logger import log_event
import config

REPORT_DIR = config.WORKSPACE_DIR / "reports"
TICKET_DIR = config.WORKSPACE_DIR / "tickets"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
TICKET_DIR.mkdir(parents=True, exist_ok=True)


class AutomationAgent:
    def run(self, task_id: str, final_synthesis: dict, human_feedback: str = "") -> list[AutomationResult]:
        """Execute approved automation actions."""
        log_event("agent_start", "automation_agent", task_id)
        results: list[AutomationResult] = []

        # ── Action 1: Save investigation report ──
        try:
            report_md = self._build_report_markdown(task_id, final_synthesis, human_feedback)
            report_path = REPORT_DIR / f"{task_id}.md"
            report_path.write_text(report_md, encoding="utf-8")

            results.append(
                AutomationResult(
                    success=True,
                    action_type="save_report",
                    output_reference=str(report_path),
                )
            )
            log_event("action_executed", "automation_agent", task_id, data={"action": "save_report", "path": str(report_path)})
        except Exception as e:
            results.append(
                AutomationResult(success=False, action_type="save_report", error=str(e))
            )

        # ── Action 2: Create follow-up ticket ──
        try:
            ticket_id = f"ENG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            ticket_path = TICKET_DIR / f"{ticket_id}.json"
            ticket_payload = {
                "ticket_id": ticket_id,
                "title": f"Follow-up: Investigation {task_id}",
                "body": final_synthesis.get("final_summary", "See attached report."),
                "next_steps": final_synthesis.get("recommended_next_steps", []),
                "created_at": datetime.now().isoformat(),
                "human_feedback": human_feedback,
            }
            ticket_path.write_text(json.dumps(ticket_payload, indent=2), encoding="utf-8")

            results.append(
                AutomationResult(
                    success=True,
                    action_type="create_ticket",
                    output_reference=ticket_id,
                )
            )
            log_event("action_executed", "automation_agent", task_id, data={"action": "create_ticket", "ticket_id": ticket_id})
        except Exception as e:
            results.append(
                AutomationResult(success=False, action_type="create_ticket", error=str(e))
            )

        log_event("agent_complete", "automation_agent", task_id, data={"actions": len(results)})
        return results

    @staticmethod
    def _build_report_markdown(task_id: str, synthesis: dict, feedback: str) -> str:
        lines = [
            f"# Investigation Report: {task_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            synthesis.get("final_summary", "No summary available."),
            "",
            "## Accepted Findings",
        ]
        for f in synthesis.get("accepted_findings", []):
            lines.append(f"- {f}")

        lines.append("")
        lines.append("## Rejected Findings")
        for f in synthesis.get("rejected_findings", []):
            lines.append(f"- {f}")

        lines.append("")
        lines.append("## Unresolved Points")
        for p in synthesis.get("unresolved_points", []):
            lines.append(f"- {p}")

        lines.append("")
        lines.append("## Recommended Next Steps")
        for s in synthesis.get("recommended_next_steps", []):
            lines.append(f"- {s}")

        if feedback:
            lines.append("")
            lines.append("## Human Feedback")
            lines.append(feedback)

        return "\n".join(lines)
