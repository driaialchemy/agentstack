"""Deterministic trust governance for Phase 6."""

from __future__ import annotations

from typing import Any

from skills.skill_registry import get_skill_by_id

TRUST_LEVELS = ["trusted", "limited_trust", "untrusted", "blocked"]
TRUSTED_SOURCES = {
    "Synthetic structured database",
    "Synthetic document database",
}


def evaluate_trust(
    *,
    agent_id: str | None = None,
    skill_id: str | None = None,
    data_source: str | None = None,
    report_verified: bool | None = None,
    quarantine_count: int = 0,
    security_flags: list[str] | None = None,
    run_failures: list[str] | None = None,
    agent_registry_path=None,
    skill_registry_path=None,
) -> dict[str, Any]:
    """Return structured trust evaluation with level, reasons, and recommended_action."""
    from agents.agent_registry import get_agent_by_id

    reasons: list[str] = []
    level = "trusted"
    recommended_action = "allow"

    if agent_id:
        agent = get_agent_by_id(agent_id, agent_registry_path)
        if agent is None:
            level = "blocked"
            reasons.append(f"Agent '{agent_id}' is not registered.")
            recommended_action = "block"
        elif not agent.get("enabled", False):
            level = "blocked"
            reasons.append(f"Agent '{agent_id}' is disabled.")
            recommended_action = "block"

    if skill_id and level != "blocked":
        skill = get_skill_by_id(skill_id, skill_registry_path)
        if skill is None:
            level = "untrusted"
            reasons.append(f"Skill '{skill_id}' is not registered.")
            recommended_action = "block"
        elif not skill.get("enabled", False):
            level = "blocked"
            reasons.append(f"Skill '{skill_id}' is disabled.")
            recommended_action = "block"
        elif agent_id and skill.get("allowed_agents"):
            if agent_id not in skill["allowed_agents"]:
                level = "blocked"
                reasons.append(
                    f"Agent '{agent_id}' is not authorized for skill '{skill_id}'."
                )
                recommended_action = "block"

    if data_source and level not in {"blocked", "untrusted"}:
        if data_source not in TRUSTED_SOURCES:
            level = "limited_trust"
            reasons.append(f"Data source '{data_source}' is not in trusted demo sources.")
            recommended_action = "review"

    if report_verified is False and level == "trusted":
        level = "limited_trust"
        reasons.append("Report verification failed or incomplete.")
        recommended_action = "review"

    if quarantine_count > 0 and level != "blocked":
        level = "limited_trust"
        reasons.append(f"{quarantine_count} quarantined output(s) in run context.")
        recommended_action = "review"

    for flag in security_flags or []:
        if level != "blocked":
            level = "untrusted"
            reasons.append(f"Security flag present: {flag}.")
            recommended_action = "block"

    if run_failures and level == "trusted":
        level = "limited_trust"
        reasons.append(f"Run recorded {len(run_failures)} failure(s).")
        recommended_action = "review"

    if not reasons:
        reasons.append("All deterministic trust checks passed.")

    return {
        "trust_level": level,
        "reasons": reasons,
        "recommended_action": recommended_action,
    }
