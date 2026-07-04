"""Policy engine for Phase 2 skill authorization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from skills.skill_registry import get_skill_by_id


@dataclass
class PolicyResult:
    allowed: bool
    reason: str
    policy_decision: str
    skill_id: str
    risk_level: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_policy(
    *,
    skill_id: str,
    charter_complete: bool,
    data_source: str,
    workflow_type: str,
    input_size: int,
    registry_path: Path | None = None,
    approved_skills: list[str] | None = None,
) -> PolicyResult:
    """Authorize or deny a requested skill execution."""
    base = {
        "skill_id": skill_id,
        "risk_level": None,
    }

    if not charter_complete:
        return PolicyResult(
            allowed=False,
            reason="Workflow charter is incomplete.",
            policy_decision="deny_charter_incomplete",
            **base,
        )

    skill = get_skill_by_id(skill_id, registry_path)
    if skill is None:
        return PolicyResult(
            allowed=False,
            reason=f"Skill '{skill_id}' is not registered.",
            policy_decision="deny_skill_not_found",
            **base,
        )

    base["risk_level"] = skill["risk_level"]

    if not skill.get("enabled", False):
        return PolicyResult(
            allowed=False,
            reason=f"Skill '{skill_id}' is disabled.",
            policy_decision="deny_skill_disabled",
            **base,
        )

    if data_source not in skill["allowed_data_sources"]:
        return PolicyResult(
            allowed=False,
            reason=(
                f"Data source '{data_source}' is not allowed for skill '{skill_id}'."
            ),
            policy_decision="deny_data_source_mismatch",
            **base,
        )

    if workflow_type not in skill["allowed_workflow_types"]:
        return PolicyResult(
            allowed=False,
            reason=(
                f"Workflow type '{workflow_type}' is not allowed for skill '{skill_id}'."
            ),
            policy_decision="deny_workflow_mismatch",
            **base,
        )

    max_size = skill["max_records_or_documents"]
    if input_size > max_size:
        return PolicyResult(
            allowed=False,
            reason=(
                f"Input size {input_size} exceeds maximum {max_size} "
                f"for skill '{skill_id}'."
            ),
            policy_decision="deny_input_size_exceeded",
            **base,
        )

    if skill.get("requires_approval", False):
        if approved_skills and skill_id in approved_skills:
            pass
        else:
            return PolicyResult(
                allowed=False,
                reason=(
                    f"Skill '{skill_id}' requires human approval, "
                    "which is not available in Phase 2."
                ),
                policy_decision="deny_approval_required",
                **base,
            )

    return PolicyResult(
        allowed=True,
        reason="Skill execution authorized by policy.",
        policy_decision="allow",
        **base,
    )
