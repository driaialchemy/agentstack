"""RecoveryAgent — governed memory and recovery skills."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent


class RecoveryAgent(BaseAgent):
    agent_id = "recovery_agent"
    default_skill_id = "create_checkpoint"

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        if override_skill_id:
            return override_skill_id
        return str(context.get("recovery_skill_id") or self.default_skill_id)

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") != "success":
            return
        output = step_result.get("output", {})
        skill_id = step_result.get("skill_id", "")
        if skill_id == "create_checkpoint":
            context["last_checkpoint"] = output
            context["last_checkpoint_id"] = output.get("checkpoint_id")
        elif skill_id == "resume_from_checkpoint":
            context["resume_state"] = output
        elif skill_id == "rollback_to_checkpoint":
            context["rollback_state"] = output
        elif skill_id == "write_dead_letter":
            context["dead_letter_entry"] = output
        elif skill_id == "quarantine_output":
            context["last_quarantine_entry"] = output
