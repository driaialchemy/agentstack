"""Base agent for Phase 3 governed execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from governance.audit_logger import log_agent_event
from governance.result_contract import enrich_governed_result, failure_class_for_policy
from skills.skill_executor import execute_skill


class BaseAgent:
    """Shared behavior for governed agents that call skills through the executor."""

    agent_id: str = ""
    default_skill_id: str = ""

    def __init__(self, agent_config: dict[str, Any]):
        self.config = agent_config
        self.agent_id = str(agent_config.get("agent_id", self.__class__.agent_id))

    @property
    def agent_name(self) -> str:
        return str(self.config.get("agent_name", self.agent_id))

    def is_enabled(self) -> bool:
        return bool(self.config.get("enabled"))

    def can_use_skill(self, skill_id: str) -> bool:
        return skill_id in self.config.get("allowed_skills", [])

    def resolve_skill_id(self, context: dict[str, Any], override_skill_id: str | None = None) -> str:
        """Return the skill this agent should call."""
        if override_skill_id:
            return override_skill_id
        return self.default_skill_id

    def run(
        self,
        *,
        context: dict[str, Any],
        skill_id_override: str | None = None,
        reports_dir: Path | None = None,
        log_path: Path | None = None,
        registry_path: Path | None = None,
    ) -> dict[str, Any]:
        """Execute one governed agent step."""
        skill_id = self.resolve_skill_id(context, skill_id_override)

        if not self.is_enabled():
            return self._deny_step(
                context=context,
                skill_id=skill_id,
                reason=f"Agent '{self.agent_id}' is disabled.",
                execution_status="denied",
                policy_decision="deny_agent_disabled",
                log_path=log_path,
            )

        if not self.can_use_skill(skill_id):
            return self._deny_step(
                context=context,
                skill_id=skill_id,
                reason=(
                    f"Agent '{self.agent_id}' is not authorized to use skill '{skill_id}'."
                ),
                execution_status="denied",
                policy_decision="deny_unauthorized_skill",
                log_path=log_path,
            )

        skill_result = execute_skill(
            run_id=context["run_id"],
            skill_id=skill_id,
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            charter_complete=context["charter_complete"],
            accountability_owner=context["accountability_owner"],
            input_size=context.get("input_size"),
            agent_context=context,
            reports_dir=reports_dir,
            registry_path=registry_path,
            log_path=log_path,
        )

        policy = skill_result.get("policy", {})
        pre_status = self._extract_gate_status(skill_result.get("pre_gates"))
        post_status = self._extract_gate_status(skill_result.get("post_gates"), default="skipped")

        if skill_result.get("status") == "denied":
            return self._finalize_step(
                context=context,
                skill_id=skill_id,
                skill_result=skill_result,
                execution_status="denied",
                policy_decision=policy.get("policy_decision", "deny"),
                pre_gate_status=pre_status,
                post_gate_status=post_status,
                output_summary=skill_result.get("reason", "Skill denied."),
                log_path=log_path,
            )

        if skill_result.get("status") != "success":
            return self._finalize_step(
                context=context,
                skill_id=skill_id,
                skill_result=skill_result,
                execution_status="error",
                policy_decision=policy.get("policy_decision", "error"),
                pre_gate_status=pre_status,
                post_gate_status=post_status or "failed",
                output_summary=skill_result.get("error", "Skill execution failed."),
                log_path=log_path,
            )

        output = skill_result.get("output", {})
        return self._finalize_step(
            context=context,
            skill_id=skill_id,
            skill_result=skill_result,
            execution_status="success",
            policy_decision=policy.get("policy_decision", "allow"),
            pre_gate_status=pre_status,
            post_gate_status=post_status,
            output_summary=self.build_output_summary(output),
            log_path=log_path,
            step_output=output,
        )

    def build_output_summary(self, output: dict[str, Any]) -> str:
        """Create a short summary string for audit logging."""
        return output.get("message") or output.get("summary_text") or f"{self.agent_name} step completed."

    def update_context(self, context: dict[str, Any], step_result: dict[str, Any]) -> None:
        """Optional hook for subclasses to store step output in shared context."""

    @staticmethod
    def _extract_gate_status(gates: list[dict[str, Any]] | None, default: str = "failed") -> str:
        if not gates:
            return default
        return "passed" if all(gate.get("passed") for gate in gates) else "failed"

    def _deny_step(
        self,
        *,
        context: dict[str, Any],
        skill_id: str,
        reason: str,
        execution_status: str,
        policy_decision: str,
        log_path: Path | None,
    ) -> dict[str, Any]:
        audit_event = log_agent_event(
            run_id=context["run_id"],
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            skill_id=skill_id,
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            policy_decision=policy_decision,
            pre_gate_status="failed",
            post_gate_status="skipped",
            execution_status=execution_status,
            output_summary=reason,
            accountability_owner=context["accountability_owner"],
            log_path=log_path,
            failure_class=failure_class_for_policy(policy_decision),
        )
        return enrich_governed_result(
            {
                "status": execution_status,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "skill_id": skill_id,
                "reason": reason,
                "policy_decision": policy_decision,
                "pre_gate_status": "failed",
                "post_gate_status": "skipped",
                "execution_status": execution_status,
                "output_summary": reason,
                "audit_event": audit_event,
                "run_id": context["run_id"],
                "workflow_type": context["workflow_type"],
                "data_source": context["data_source"],
                "accountability_owner": context["accountability_owner"],
            },
            failure_class=failure_class_for_policy(policy_decision),
        )

    def _finalize_step(
        self,
        *,
        context: dict[str, Any],
        skill_id: str,
        skill_result: dict[str, Any],
        execution_status: str,
        policy_decision: str,
        pre_gate_status: str,
        post_gate_status: str,
        output_summary: str,
        log_path: Path | None,
        step_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        audit_event = log_agent_event(
            run_id=context["run_id"],
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            skill_id=skill_id,
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            policy_decision=policy_decision,
            pre_gate_status=pre_gate_status,
            post_gate_status=post_gate_status,
            execution_status=execution_status,
            output_summary=output_summary,
            accountability_owner=context["accountability_owner"],
            log_path=log_path,
        )
        return enrich_governed_result(
            {
                "status": "success" if execution_status == "success" else execution_status,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "skill_id": skill_id,
                "execution_status": execution_status,
                "policy_decision": policy_decision,
                "pre_gate_status": pre_gate_status,
                "post_gate_status": post_gate_status,
                "output_summary": output_summary,
                "policy": skill_result.get("policy"),
                "pre_gates": skill_result.get("pre_gates", []),
                "post_gates": skill_result.get("post_gates", []),
                "skill_result": skill_result,
                "output": step_output,
                "report_path": skill_result.get("report_path"),
                "audit_event": audit_event,
                "run_id": context["run_id"],
                "workflow_type": context["workflow_type"],
                "data_source": context["data_source"],
                "accountability_owner": context["accountability_owner"],
            },
            failure_class=skill_result.get("failure_class"),
        )
