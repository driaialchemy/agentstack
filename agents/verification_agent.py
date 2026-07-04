"""VerificationAgent — verify analysis output without modifying it."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from skills.skill_executor import ANALYTICS_WORKFLOW


class VerificationAgent(BaseAgent):
    agent_id = "verification_agent"
    default_skill_id = "output_verification"

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        if override_skill_id:
            return override_skill_id
        if context.get("workflow_type") == ANALYTICS_WORKFLOW:
            return "verify_analytics_report"
        return self.default_skill_id

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") == "success":
            context["verification_output"] = step_result.get("output", {})
            if context.get("workflow_type") == ANALYTICS_WORKFLOW:
                context["analytics_verified"] = True
