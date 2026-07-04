"""Policy coverage evidence report."""

from __future__ import annotations

from typing import Any


def build_policy_coverage_report(*, run_context: dict[str, Any]) -> dict[str, Any]:
    agent_steps = run_context.get("agent_steps", [])
    memory_actions = run_context.get("memory_actions", [])
    governance_actions = run_context.get("governance_actions", [])

    policies: list[dict[str, Any]] = []
    for step in agent_steps:
        policy = step.get("policy") or {}
        policies.append(
            {
                "skill_id": step.get("skill_id"),
                "agent_id": step.get("agent_id"),
                "policy_decision": policy.get("policy_decision", step.get("policy_decision")),
                "status": "passed" if step.get("execution_status") == "success" else "failed",
                "reason": policy.get("reason") or step.get("output_summary", ""),
            }
        )
    for action in memory_actions + governance_actions:
        policy = action.get("policy") or {}
        policies.append(
            {
                "skill_id": action.get("skill_id"),
                "agent_id": "governance",
                "policy_decision": policy.get("policy_decision", "unknown"),
                "status": action.get("status", "unknown"),
                "reason": policy.get("reason") or action.get("reason", ""),
            }
        )

    return {
        "run_id": run_context.get("run_id"),
        "policies_evaluated": len(policies),
        "policies": policies,
        "passed_count": sum(1 for item in policies if item["status"] in {"success", "passed"}),
        "failed_count": sum(1 for item in policies if item["status"] not in {"success", "passed"}),
    }
