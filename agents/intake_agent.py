"""IntakeAgent — validate workflow pairing and prepare intake summary."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent


class IntakeAgent(BaseAgent):
    agent_id = "intake_agent"
    default_skill_id = "intake_summary"

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") == "success":
            context["intake_output"] = step_result.get("output", {})
