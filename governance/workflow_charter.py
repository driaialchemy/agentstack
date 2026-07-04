"""Workflow charter helpers for Phase 1 — no charter, no run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CHARTER_PATH = REPO_ROOT / "AGENT_CHARTER.md"

CHARTER_RULE = "No charter, no run."

DATA_SOURCES = [
    "Synthetic structured database",
    "Synthetic document database",
]

WORKFLOW_TYPES = [
    "Structured data preview",
    "Document review preview",
    "Structured data analytics",
]

REQUIRED_CHARTER_FIELDS = [
    ("business_problem_ack", "Business problem acknowledged"),
    ("desired_outcome_ack", "Desired outcome acknowledged"),
    ("accountability_owner", "Accountability owner named"),
    ("workflow_scope_ack", "Workflow scope confirmed"),
    ("out_of_scope_ack", "Out-of-scope activities excluded"),
    ("audit_enabled_ack", "Audit and observability enabled"),
]


def load_charter_text() -> str:
    """Load the repository agent charter markdown."""
    try:
        return CHARTER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to read AGENT_CHARTER.md: {exc}") from exc


def validate_charter(form_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return whether the run charter checklist is complete."""
    missing: list[str] = []

    for field_name, label in REQUIRED_CHARTER_FIELDS:
        value = form_data.get(field_name)
        if field_name == "accountability_owner":
            if not str(value or "").strip():
                missing.append(label)
        elif not value:
            missing.append(label)

    return len(missing) == 0, missing


def charter_status_message(is_complete: bool, missing: list[str]) -> str:
    """Human-readable charter validation message."""
    if is_complete:
        return "Charter complete. Workflow may run."
    if missing:
        return f"{CHARTER_RULE} Missing: {', '.join(missing)}."
    return CHARTER_RULE
