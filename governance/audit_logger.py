"""JSONL audit logger for Phase 1 workflow runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT_LOG_PATH = REPO_ROOT / "storage" / "audit_log.jsonl"


def generate_run_id() -> str:
    """Create a unique run identifier."""
    return str(uuid4())


def _ensure_log_directory(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)


def log_event(
    *,
    run_id: str,
    workflow_type: str,
    data_source: str,
    action: str,
    status: str,
    summary: str,
    log_path: Path | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Append one audit event to the JSONL log."""
    target_path = log_path or DEFAULT_AUDIT_LOG_PATH
    _ensure_log_directory(target_path)

    event: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow_type": workflow_type,
        "data_source": data_source,
        "action": action,
        "status": status,
        "summary": summary,
    }
    event.update(extra)

    try:
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")
    except OSError as exc:
        raise RuntimeError(f"Failed to write audit log: {exc}") from exc

    return event


def read_audit_events(
    log_path: Path | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Read audit events from the JSONL log, newest last."""
    target_path = log_path or DEFAULT_AUDIT_LOG_PATH
    if not target_path.exists():
        return []

    events: list[dict[str, Any]] = []
    try:
        with target_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError as exc:
        raise RuntimeError(f"Failed to read audit log: {exc}") from exc

    if limit is not None:
        return events[-limit:]
    return events
