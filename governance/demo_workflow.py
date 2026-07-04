"""Basic Phase 1 demo workflow runner (no multi-agent orchestration)."""

from __future__ import annotations

from typing import Any

from data_sources.synthetic_data import get_structured_records, summarize_structured_data
from data_sources.synthetic_documents import get_documents, summarize_documents
from governance.audit_logger import log_event


def build_structured_output(*, workflow_type: str, data_source: str) -> dict[str, Any]:
    """Build structured data preview output (Phase 1 logic, no audit)."""
    if data_source != "Synthetic structured database":
        raise ValueError("Structured data preview requires the synthetic structured database.")
    if workflow_type != "Structured data preview":
        raise ValueError("Invalid workflow type for structured data preview.")

    records = get_structured_records()
    summary = summarize_structured_data()
    return {
        "workflow_type": workflow_type,
        "data_source": data_source,
        "summary": summary,
        "records": records,
    }


def build_document_output(*, workflow_type: str, data_source: str) -> dict[str, Any]:
    """Build document review preview output (Phase 1 logic, no audit)."""
    if data_source != "Synthetic document database":
        raise ValueError("Document review preview requires the synthetic document database.")
    if workflow_type != "Document review preview":
        raise ValueError("Invalid workflow type for document review preview.")

    documents = get_documents()
    summary = summarize_documents()
    return {
        "workflow_type": workflow_type,
        "data_source": data_source,
        "summary": summary,
        "documents": documents,
    }


def run_demo_workflow(
    *,
    run_id: str,
    workflow_type: str,
    data_source: str,
    accountability_owner: str,
) -> dict[str, Any]:
    """
    Execute a simple demonstration workflow and write audit events.

    This is intentionally linear: no agents, no orchestrator, no direct agent calls.
    """
    events: list[dict[str, Any]] = []

    def _log(action: str, status: str, summary: str, **extra: Any) -> None:
        event = log_event(
            run_id=run_id,
            workflow_type=workflow_type,
            data_source=data_source,
            action=action,
            status=status,
            summary=summary,
            accountability_owner=accountability_owner,
            **extra,
        )
        events.append(event)

    _log("workflow_started", "success", "Demo workflow started.")

    try:
        if workflow_type == "Structured data preview":
            output = build_structured_output(
                workflow_type=workflow_type,
                data_source=data_source,
            )
            _log(
                "load_structured_data",
                "success",
                f"Loaded {len(output['records'])} synthetic structured records.",
            )
        elif workflow_type == "Document review preview":
            output = build_document_output(
                workflow_type=workflow_type,
                data_source=data_source,
            )
            _log(
                "load_documents",
                "success",
                f"Loaded {len(output['documents'])} synthetic documents.",
            )
        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        _log(
            "workflow_completed",
            "success",
            "Demo workflow completed successfully.",
        )
        return {"status": "success", "output": output, "events": events}

    except Exception as exc:
        _log(
            "workflow_failed",
            "error",
            f"Demo workflow failed: {exc}",
        )
        return {
            "status": "error",
            "error": str(exc),
            "events": events,
        }
