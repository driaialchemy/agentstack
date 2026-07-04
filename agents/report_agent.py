"""ReportAgent — produce governed workflow or analytics reports."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from skills.skill_executor import ANALYTICS_WORKFLOW


class ReportAgent(BaseAgent):
    agent_id = "report_agent"
    default_skill_id = "governed_workflow_summary"

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        if override_skill_id:
            return override_skill_id
        if context.get("workflow_type") == ANALYTICS_WORKFLOW:
            return "generate_analytics_report"
        return self.default_skill_id

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") != "success":
            return

        output = step_result.get("output", {})
        if context.get("workflow_type") == ANALYTICS_WORKFLOW:
            context["analytics_report"] = output
            context["report_path"] = output.get("json_path")
            context["final_summary"] = {
                "summary_text": "Analytics report generated and ready for verification.",
                "markdown_path": output.get("markdown_path"),
                "html_path": output.get("html_path"),
            }
        else:
            context["final_summary"] = output
