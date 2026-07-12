"""
Structured audit logger.

Every agent action writes a JSONL event to audit/events.jsonl.
Uses Python's logging module with a RotatingFileHandler, which is
thread-safe and handles log rotation automatically.
"""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import config

AUDIT_FILE = config.AUDIT_LOG
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

# One logger, one handler, configured once at import time
_audit_logger = logging.getLogger("autoagent.audit")
if not _audit_logger.handlers:
    _handler = RotatingFileHandler(
        AUDIT_FILE,
        maxBytes=10_000_000,   # 10 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(_handler)
    _audit_logger.setLevel(logging.INFO)
    _audit_logger.propagate = False


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
    _audit_logger.info(json.dumps(event))
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
