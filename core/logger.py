"""
Structured audit logger.

Every agent action writes a JSONL event to audit/events.jsonl.
This provides full traceability for the investigation pipeline.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import config


AUDIT_FILE = config.AUDIT_LOG
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_event(
    event_type: str,
    agent: str,
    task_id: str,
    data: dict | None = None,
    status: str = "ok",
) -> dict:
    """Append a structured event to the audit log and return it."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "agent": agent,
        "task_id": task_id,
        "status": status,
        "data": data or {},
    }

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    return event


def read_audit_log(task_id: str | None = None) -> list[dict]:
    """Read audit events, optionally filtered by task_id."""
    if not AUDIT_FILE.exists():
        return []

    events = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if task_id is None or event.get("task_id") == task_id:
                events.append(event)
    return events
