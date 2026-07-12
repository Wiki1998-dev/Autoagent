"""
Automation MCP Server.

Handles approved output actions:
  - save_report  → writes markdown to workspace/reports/
  - create_ticket → writes JSON to workspace/tickets/

Uses FastMCP lifespan to create directories at startup (not at import time).
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone

from fastmcp import FastMCP
from pydantic import BaseModel, Field
import config

REPORT_DIR = config.WORKSPACE_DIR / "reports"
TICKET_DIR = config.WORKSPACE_DIR / "tickets"


@asynccontextmanager
async def lifespan(server):
    """Create output directories once at server startup."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TICKET_DIR.mkdir(parents=True, exist_ok=True)
    yield


mcp = FastMCP("automation-server", lifespan=lifespan)


# ── Response models ───────────────────────────────────────────

class SaveReportResult(BaseModel):
    success: bool
    path: str

class CreateTicketResult(BaseModel):
    success: bool
    ticket_id: str
    path: str


# ── Tools ─────────────────────────────────────────────────────

@mcp.tool()
def save_report(
    task_id: str = Field(description="Investigation task ID used as the filename"),
    report_markdown: str = Field(description="Full investigation report in Markdown format"),
) -> SaveReportResult:
    """Save a markdown investigation report to workspace/reports/<task_id>.md."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    # Prevent path traversal by extracting only the filename
    safe_name = Path(task_id).name
    path = REPORT_DIR / f"{safe_name}.md"

    # Backup if exists
    if path.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_path = REPORT_DIR / f"{safe_name}_backup_{timestamp}.md"
        try:
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass

    path.write_text(report_markdown, encoding="utf-8")
    return SaveReportResult(success=True, path=str(path))


@mcp.tool()
def create_ticket(
    title: str = Field(description="Short title for the engineering ticket"),
    body: str = Field(description="Full investigation summary or follow-up description"),
    metadata: dict = Field(default_factory=dict, description="Additional key/value metadata (task_id, next_steps, etc.)"),
) -> CreateTicketResult:
    """Create an engineering follow-up ticket and persist it to workspace/tickets/."""
    TICKET_DIR.mkdir(parents=True, exist_ok=True)
    ticket_id = f"ENG-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    path = TICKET_DIR / f"{ticket_id}.json"
    payload = {
        "ticket_id": ticket_id,
        "title": title,
        "body": body,
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return CreateTicketResult(success=True, ticket_id=ticket_id, path=str(path))
