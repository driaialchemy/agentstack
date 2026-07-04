"""AnalysisAgent — run governed structured or document analysis skills."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from skills.skill_executor import ANALYTICS_WORKFLOW, resolve_skill_for_workflow


class AnalysisAgent(BaseAgent):
    agent_id = "analysis_agent"

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        if override_skill_id:
            return override_skill_id
        if context.get("workflow_type") == ANALYTICS_WORKFLOW:
            return "run_eda"
        return resolve_skill_for_workflow(context["workflow_type"])

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") != "success":
            return

        skill_id = step_result.get("skill_id", "")
        output = step_result.get("output", {})
        skill_result = step_result.get("skill_result", {})

        if skill_id == "run_eda":
            context["eda_result"] = output
        elif skill_id == "run_regression":
            context["regression_result"] = output
        elif skill_id == "run_fourier_forecast":
            context["forecast_result"] = output
        elif skill_id == "generate_chart":
            context["chart_result"] = output
        elif skill_id in {"structured_data_summary", "document_review_summary"}:
            context["analysis_result"] = skill_result
            context["analysis_output"] = output
            if step_result.get("report_path"):
                context["report_path"] = step_result["report_path"]

        if context.get("workflow_type") == ANALYTICS_WORKFLOW:
            context["analytics_results"] = {
                "eda": context.get("eda_result"),
                "regression": context.get("regression_result"),
                "forecast": context.get("forecast_result"),
                "chart": context.get("chart_result"),
            }
