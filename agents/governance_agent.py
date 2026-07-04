"""GovernanceAgent — Phase 6 advanced governance and evidence skills."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent


class GovernanceAgent(BaseAgent):
    agent_id = "governance_agent"
    default_skill_id = "generate_governance_run_summary"

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        if override_skill_id:
            return override_skill_id
        return str(context.get("governance_skill_id") or self.default_skill_id)

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        if step_result.get("status") != "success":
            return
        output = step_result.get("output", {})
        skill_id = step_result.get("skill_id", "")
        if skill_id == "generate_governance_run_summary":
            context["governance_summary"] = output
            context["evidence_export_paths"] = output.get("export_paths", {})
        elif skill_id == "evaluate_cost":
            context["cost_summary"] = output.get("cost_summary", output)
        elif skill_id == "evaluate_trust":
            context["trust_summary"] = output
        elif skill_id == "run_security_check":
            context["security_summary"] = output
        elif skill_id in {"request_human_approval", "resolve_human_approval"}:
            records = list(context.get("approval_records") or [])
            records.append(output)
            context["approval_records"] = records
        elif skill_id == "create_incident_report":
            incidents = list(context.get("incidents") or [])
            incidents.append(output)
            context["incidents"] = incidents
