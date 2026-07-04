"""Validate memory writes before persisting governed context."""

from __future__ import annotations

from typing import Any


def validate_memory_write(
    payload: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, str, str | None]:
    """
    Return (allowed, reason, failure_class).

    Hard rule: validate before memory write.
    """
    run_id = str(payload.get("run_id") or context.get("run_id") or "").strip()
    if not run_id:
        return False, "run_id is required for memory write.", "MEMORY_FAILURE"

    owner = str(
        payload.get("accountability_owner") or context.get("accountability_owner") or ""
    ).strip()
    if not owner:
        return False, "accountability owner is required for memory write.", "GOVERNANCE_FAILURE"

    if not context.get("charter_complete", False):
        return False, "Charter must be complete before memory write.", "GOVERNANCE_FAILURE"

    if not isinstance(payload, dict) or not payload.get("structured", False):
        return False, "Memory payload must be structured.", "MEMORY_FAILURE"

    if payload.get("status") == "failed" or payload.get("failed") is True:
        return False, "Failed output cannot be written to memory.", "MEMORY_FAILURE"

    if payload.get("failure_class"):
        return False, "Output with failure class cannot be written to memory.", "MEMORY_FAILURE"

    if payload.get("verification_required") and not payload.get("verified"):
        return False, "Unverified output cannot be written to memory.", "QUARANTINE_FAILURE"

    payload_workflow = payload.get("workflow_type")
    payload_source = payload.get("data_source")
    if payload_workflow and payload_workflow != context.get("workflow_type"):
        return False, "Output workflow type does not match current run context.", "MEMORY_FAILURE"
    if payload_source and payload_source != context.get("data_source"):
        return False, "Output data source does not match current run context.", "MEMORY_FAILURE"

    return True, "Memory write validated.", None
