"""
Automation MCP Server.

Handles approved output actions:
  - save_report  → writes markdown to workspace/reports/
  - create_ticket → writes JSON to workspace/tickets/
"""

import json
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
import config

mcp = FastMCP("automation-server")

REPORT_DIR = config.WORKSPACE_DIR / "reports"
TICKET_DIR = config.WORKSPACE_DIR / "tickets"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
TICKET_DIR.mkdir(parents=True, exist_ok=True)


@mcp.tool()
def save_report(task_id: str, report_markdown: str) -> dict:
    """Save a markdown investigation report."""
    path = REPORT_DIR / f"{task_id}.md"
    path.write_text(report_markdown, encoding="utf-8")
    return {"success": True, "path": str(path)}


@mcp.tool()
def create_ticket(title: str, body: str, metadata: dict) -> dict:
    """Create an engineering follow-up ticket."""
    ticket_id = f"ENG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    path = TICKET_DIR / f"{ticket_id}.json"
    payload = {
        "ticket_id": ticket_id,
        "title": title,
        "body": body,
        "metadata": metadata,
        "created_at": datetime.now().isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"success": True, "ticket_id": ticket_id, "path": str(path)}
