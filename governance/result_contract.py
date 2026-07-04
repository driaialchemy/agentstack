"""Standard governed result envelope for major workflow responses."""

from __future__ import annotations

from typing import Any

from governance.failure_taxonomy import recommended_action

POLICY_FAILURE_CLASS: dict[str, str] = {
    "deny_charter_incomplete": "GOVERNANCE_FAILURE",
    "deny_skill_not_found": "SKILL_FAILURE",
    "deny_skill_disabled": "SKILL_FAILURE",
    "deny_data_source_mismatch": "DATA_SOURCE_FAILURE",
    "deny_workflow_mismatch": "GOVERNANCE_FAILURE",
    "deny_input_size_exceeded": "GOVERNANCE_FAILURE",
    "deny_approval_required": "APPROVAL_FAILURE",
    "deny_unknown_agent": "AGENT_FAILURE",
    "deny_unauthorized_skill": "AGENT_FAILURE",
    "deny_agent_disabled": "AGENT_FAILURE",
}


def failure_class_for_policy(policy_decision: str | None) -> str | None:
    if not policy_decision:
        return None
    return POLICY_FAILURE_CLASS.get(policy_decision)


def _extract_evidence_refs(result: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    export_paths = result.get("evidence_export_paths") or {}
    if isinstance(export_paths, dict):
        refs.extend(str(path) for path in export_paths.values() if path)
    summary = result.get("governance_summary") or {}
    if isinstance(summary, dict):
        paths = summary.get("export_paths")
        if isinstance(paths, dict):
            refs.extend(str(path) for path in paths.values() if path)
    return refs


def _extract_audit_refs(result: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for event in result.get("events") or []:
        if isinstance(event, dict) and event.get("timestamp"):
            refs.append(f"{event.get('action')}:{event.get('timestamp')}")
    audit_event = result.get("audit_event")
    if isinstance(audit_event, dict) and audit_event.get("timestamp"):
        refs.append(f"{audit_event.get('action')}:{audit_event.get('timestamp')}")
    return refs


def enrich_governed_result(
    result: dict[str, Any],
    *,
    failure_class: str | None = None,
    recommended: str | None = None,
) -> dict[str, Any]:
    """Attach standard governed fields without removing legacy keys."""
    status = str(result.get("status", "unknown"))
    success = status == "success"
    message = (
        result.get("message")
        or result.get("reason")
        or result.get("error")
        or result.get("output_summary")
        or ""
    )
    policy = result.get("policy") or {}
    resolved_failure = (
        failure_class
        or result.get("failure_class")
        or failure_class_for_policy(policy.get("policy_decision") if isinstance(policy, dict) else None)
    )
    if status in {"denied", "error"} and not resolved_failure:
        resolved_failure = "GOVERNANCE_FAILURE"

    errors: list[str] = list(result.get("errors") or [])
    if result.get("error") and str(result["error"]) not in errors:
        errors.append(str(result["error"]))
    if result.get("reason") and status == "denied" and str(result["reason"]) not in errors:
        errors.append(str(result["reason"]))

    envelope: dict[str, Any] = {
        "success": success,
        "status": status,
        "message": message,
        "run_id": result.get("run_id", ""),
        "workflow_type": result.get("workflow_type", ""),
        "data_source": result.get("data_source", ""),
        "accountability_owner": result.get("accountability_owner", ""),
        "data": result.get("data") if "data" in result else result.get("output"),
        "errors": errors,
        "warnings": list(result.get("warnings") or []),
        "evidence_refs": list(result.get("evidence_refs") or _extract_evidence_refs(result)),
        "audit_refs": list(result.get("audit_refs") or _extract_audit_refs(result)),
    }
    if resolved_failure:
        envelope["failure_class"] = resolved_failure
        envelope["recommended_action"] = recommended or result.get(
            "recommended_action", recommended_action(resolved_failure)
        )

    merged = dict(result)
    merged.update(envelope)
    return merged
