"""JSONL audit logger for Phase 1 workflow runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from skills.skill_registry import get_skill_by_id

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT_LOG_PATH = REPO_ROOT / "storage" / "audit_log.jsonl"


def generate_run_id() -> str:
    """Create a unique run identifier."""
    return str(uuid4())


def _ensure_log_directory(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)


def _skill_version(skill_id: str | None, registry_path: Path | None = None) -> str | None:
    if not skill_id:
        return None
    skill = get_skill_by_id(skill_id, registry_path)
    if skill is None:
        return None
    return str(skill.get("version", "1.0.0"))


def _gate_result_label(pre_gate_status: str | None, post_gate_status: str | None) -> str | None:
    if pre_gate_status is None and post_gate_status is None:
        return None
    return f"{pre_gate_status or 'not_applicable'}/{post_gate_status or 'not_applicable'}"


def build_audit_record(
    *,
    run_id: str,
    workflow_type: str,
    data_source: str,
    action: str,
    status: str,
    summary: str,
    accountability_owner: str = "",
    skill_id: str | None = None,
    agent_id: str | None = None,
    policy_decision: str | None = None,
    pre_gate_status: str | None = None,
    post_gate_status: str | None = None,
    failure_class: str | None = None,
    approval_status: str | None = None,
    evidence_ref: str | None = None,
    skill_version: str | None = None,
    task_id: str | None = None,
    duration_ms: int | None = None,
    input_hash: str | None = None,
    output_hash: str | None = None,
    registry_path: Path | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a normalized audit record with applicable fields only."""
    event: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow_type": workflow_type,
        "data_source": data_source,
        "action": action,
        "status": status,
        "summary": summary,
    }

    if accountability_owner:
        event["accountability_owner"] = accountability_owner
    if agent_id:
        event["agent_id"] = agent_id
    if skill_id:
        event["skill_id"] = skill_id
        resolved_version = skill_version or _skill_version(skill_id, registry_path)
        if resolved_version:
            event["skill_version"] = resolved_version
    if task_id:
        event["task_id"] = task_id
    elif skill_id or agent_id:
        event["task_id"] = f"{skill_id or agent_id}:{action}"

    if policy_decision:
        event["policy_decision"] = policy_decision

    gate_result = _gate_result_label(pre_gate_status, post_gate_status)
    if gate_result:
        event["gate_result"] = gate_result
    if pre_gate_status is not None:
        event["pre_gate_status"] = pre_gate_status
    if post_gate_status is not None:
        event["post_gate_status"] = post_gate_status

    if failure_class:
        event["failure_class"] = failure_class
    if approval_status:
        event["approval_status"] = approval_status
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    if input_hash:
        event["input_hash"] = input_hash
    if output_hash:
        event["output_hash"] = output_hash
    if evidence_ref:
        event["evidence_ref"] = evidence_ref

    event.update(extra)
    return event


def log_event(
    *,
    run_id: str,
    workflow_type: str,
    data_source: str,
    action: str,
    status: str,
    summary: str,
    log_path: Path | None = None,
    registry_path: Path | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Append one audit event to the JSONL log."""
    target_path = log_path or DEFAULT_AUDIT_LOG_PATH
    _ensure_log_directory(target_path)

    event = build_audit_record(
        run_id=run_id,
        workflow_type=workflow_type,
        data_source=data_source,
        action=action,
        status=status,
        summary=summary,
        registry_path=registry_path,
        **extra,
    )

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


def log_agent_event(
    *,
    run_id: str,
    agent_id: str,
    agent_name: str,
    skill_id: str,
    workflow_type: str,
    data_source: str,
    policy_decision: str,
    pre_gate_status: str,
    post_gate_status: str,
    execution_status: str,
    output_summary: str,
    accountability_owner: str,
    log_path: Path | None = None,
    registry_path: Path | None = None,
    failure_class: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Append a Phase 3 agent-step audit event (Phase 1/2 fields preserved)."""
    return log_event(
        run_id=run_id,
        workflow_type=workflow_type,
        data_source=data_source,
        action="agent_step",
        status=execution_status,
        summary=output_summary,
        log_path=log_path,
        registry_path=registry_path,
        accountability_owner=accountability_owner,
        agent_id=agent_id,
        agent_name=agent_name,
        skill_id=skill_id,
        policy_decision=policy_decision,
        pre_gate_status=pre_gate_status,
        post_gate_status=post_gate_status,
        execution_status=execution_status,
        output_summary=output_summary,
        failure_class=failure_class,
        **extra,
    )


def log_skill_event(
    *,
    run_id: str,
    accountability_owner: str,
    skill_id: str,
    workflow_type: str,
    data_source: str,
    policy_decision: str,
    pre_gate_status: str,
    post_gate_status: str,
    action: str,
    status: str,
    summary: str,
    log_path: Path | None = None,
    registry_path: Path | None = None,
    failure_class: str | None = None,
    approval_status: str | None = None,
    evidence_ref: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Append a Phase 2 skill execution audit event (Phase 1 fields preserved)."""
    return log_event(
        run_id=run_id,
        workflow_type=workflow_type,
        data_source=data_source,
        action=action,
        status=status,
        summary=summary,
        log_path=log_path,
        registry_path=registry_path,
        accountability_owner=accountability_owner,
        skill_id=skill_id,
        policy_decision=policy_decision,
        pre_gate_status=pre_gate_status,
        post_gate_status=post_gate_status,
        failure_class=failure_class,
        approval_status=approval_status,
        evidence_ref=evidence_ref,
        **extra,
    )
