"""Audit evidence report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from governance.audit_logger import read_audit_events


def build_audit_evidence_report(
    *,
    run_id: str,
    run_context: dict[str, Any],
    log_path: Path | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    events = read_audit_events(limit=limit, log_path=log_path)
    run_events = [event for event in events if event.get("run_id") == run_id]

    failures = [
        event for event in run_events if event.get("status") in {"error", "denied", "failed"}
    ]
    approvals = run_context.get("approval_records", [])
    checkpoints = run_context.get("checkpoints", [])
    quarantine = run_context.get("quarantine_events", [])
    dead_letter = run_context.get("dead_letter_events", [])

    return {
        "run_id": run_id,
        "event_count": len(run_events),
        "key_audit_entries": run_events[-20:],
        "failures": failures,
        "approvals": approvals,
        "checkpoints": checkpoints,
        "quarantine_events": quarantine,
        "dead_letter_events": dead_letter,
    }
