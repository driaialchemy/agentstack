"""Governance run summary and final verdict."""

from __future__ import annotations

from typing import Any

VERDICTS = ["approved", "approved_with_limitations", "blocked", "requires_human_review"]


def build_governance_run_summary(*, run_context: dict[str, Any]) -> dict[str, Any]:
    gates_passed = 0
    gates_failed = 0
    for step in run_context.get("agent_steps", []):
        if step.get("pre_gate_status") == "passed":
            gates_passed += 1
        else:
            gates_failed += 1
        if step.get("post_gate_status") == "passed":
            gates_passed += 1
        elif step.get("post_gate_status") not in {"skipped", None}:
            gates_failed += 1

    cost_summary = run_context.get("cost_summary") or {}
    trust_summary = run_context.get("trust_summary") or {}
    security_summary = run_context.get("security_summary") or {}
    approval_records = run_context.get("approval_records") or []

    approvals_required = len([item for item in approval_records if item.get("status") == "pending"]) + len(
        [item for item in approval_records if item.get("status") in {"approved", "rejected", "overridden"}]
    )
    approvals_completed = len(
        [item for item in approval_records if item.get("status") in {"approved", "overridden"}]
    )

    report_verified = bool(run_context.get("analytics_verified", True))
    if run_context.get("verification_failed"):
        report_verified = False

    verdict = _final_verdict(
        run_status=str(run_context.get("status", "unknown")),
        cost_status=str(cost_summary.get("cost_status", "within_budget")),
        trust_level=str(trust_summary.get("trust_level", "trusted")),
        security_passed=bool(security_summary.get("passed", True)),
        report_verified=report_verified,
        approval_records=approval_records,
        incidents=run_context.get("incidents") or [],
    )

    agents_used = sorted(
        {
            str(step.get("agent_id"))
            for step in run_context.get("agent_steps", [])
            if step.get("agent_id")
        }
    )
    skills_used = sorted(
        {
            str(step.get("skill_id"))
            for step in run_context.get("agent_steps", [])
            if step.get("skill_id")
        }
    )

    return {
        "run_id": run_context.get("run_id"),
        "accountability_owner": run_context.get("accountability_owner"),
        "workflow_type": run_context.get("workflow_type"),
        "data_source": run_context.get("data_source"),
        "agents_used": agents_used,
        "skills_used": skills_used,
        "gates_passed": gates_passed,
        "gates_failed": gates_failed,
        "approvals_required": approvals_required,
        "approvals_completed": approvals_completed,
        "report_verification_status": "verified" if report_verified else "failed_or_incomplete",
        "trust_level": trust_summary.get("trust_level", "trusted"),
        "cost_status": cost_summary.get("cost_status", "within_budget"),
        "security_status": "passed" if security_summary.get("passed", True) else "failed",
        "final_governance_verdict": verdict,
    }


def _final_verdict(
    *,
    run_status: str,
    cost_status: str,
    trust_level: str,
    security_passed: bool,
    report_verified: bool,
    approval_records: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
) -> str:
    if run_status in {"denied", "error"}:
        return "blocked"
    if not security_passed or trust_level == "blocked":
        return "blocked"
    if cost_status == "exceeded":
        return "blocked"
    pending = [item for item in approval_records if item.get("status") == "pending"]
    rejected = [item for item in approval_records if item.get("status") == "rejected"]
    if pending or rejected:
        return "requires_human_review"
    if incidents or trust_level in {"limited_trust", "untrusted"} or not report_verified:
        return "approved_with_limitations"
    return "approved"
