"""Skill coverage evidence report."""

from __future__ import annotations

from typing import Any

from governance.cost_tracker import skill_cost_metadata
from skills.skill_registry import get_skill_by_id


def build_skill_coverage_report(*, run_context: dict[str, Any], registry_path=None) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_skill(skill_id: str, agent_id: str, outcome: str) -> None:
        if skill_id in seen:
            return
        seen.add(skill_id)
        skill = get_skill_by_id(skill_id, registry_path) or {}
        cost = skill_cost_metadata(skill_id, registry_path)
        skills.append(
            {
                "skill_id": skill_id,
                "version": skill.get("version", "1.0.0"),
                "agent_id": agent_id,
                "risk_tier": skill.get("risk_level", "unknown"),
                "estimated_cost": cost["estimated_cost"],
                "cost_category": cost["cost_category"],
                "outcome": outcome,
            }
        )

    for step in run_context.get("agent_steps", []):
        add_skill(
            str(step.get("skill_id", "")),
            str(step.get("agent_id", "")),
            str(step.get("execution_status", "unknown")),
        )
    for action in run_context.get("memory_actions", []) + run_context.get("governance_actions", []):
        add_skill(
            str(action.get("skill_id", "")),
            "governance",
            str(action.get("status", "unknown")),
        )

    return {
        "run_id": run_context.get("run_id"),
        "skills_invoked": len(skills),
        "skills": skills,
    }
