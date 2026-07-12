"""
Structured audit logger.

Every agent action writes a JSONL event to audit/events.jsonl.
Uses Python's logging module with a RotatingFileHandler, which is
thread-safe and handles log rotation automatically.

Issue #18: read_audit_log() acquires a threading.Lock shared with the
write path so partial-line reads under concurrent append are impossible.
"""

import json
import logging
import threading
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
import config

AUDIT_FILE = config.AUDIT_LOG
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Shared lock between writer and reader (same process / multiple threads)
_audit_lock = threading.Lock()

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
    with _audit_lock:
        _audit_logger.info(json.dumps(event))
    return event


def read_audit_log(task_id: str | None = None) -> list[dict]:
    """Read audit events, optionally filtered by task_id.

    Acquires the write lock so reads are never interleaved with an active
    append (issue #18).
    """
    if not AUDIT_FILE.exists():
        return []

    events = []
    with _audit_lock:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if task_id is None or event.get("task_id") == task_id:
                    events.append(event)
    return events

