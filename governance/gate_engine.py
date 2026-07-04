"""Gate engine for Phase 2 pre- and post-execution checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from governance.policy_engine import PolicyResult
from governance.workflow_charter import DATA_SOURCES, WORKFLOW_TYPES
from skills.skill_registry import get_skill_by_id

APPROVAL_REQUIRED_SKILLS = {
    "approval_required_demo",
    "resume_from_checkpoint",
    "rollback_to_checkpoint",
    "run_security_check",
    "request_human_approval",
    "resolve_human_approval",
}

REPORT_RELEASE_SKILLS = {
    "governed_workflow_summary",
    "generate_analytics_report",
}


@dataclass
class GateResult:
    passed: bool
    gate_name: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_pre_execution_gates(
    *,
    skill_id: str,
    charter_complete: bool,
    policy: PolicyResult,
    data_source: str,
    workflow_type: str,
    registry_path: Path | None = None,
    agent_context: dict[str, Any] | None = None,
) -> list[GateResult]:
    """Run pre-execution gates before a skill executes."""
    results: list[GateResult] = []

    results.append(
        GateResult(
            passed=charter_complete,
            gate_name="CharterCompleteGate",
            reason="Charter complete" if charter_complete else "Charter incomplete",
            details={"charter_complete": charter_complete},
        )
    )

    results.append(
        GateResult(
            passed=policy.allowed,
            gate_name="PolicyAllowedGate",
            reason=policy.reason,
            details={"policy_decision": policy.policy_decision},
        )
    )

    skill = get_skill_by_id(skill_id, registry_path)
    results.append(
        GateResult(
            passed=skill is not None,
            gate_name="SkillExistsGate",
            reason="Skill registered" if skill else f"Skill '{skill_id}' not found",
            details={"skill_id": skill_id},
        )
    )

    skill_enabled = bool(skill and skill.get("enabled"))
    results.append(
        GateResult(
            passed=skill_enabled,
            gate_name="SkillEnabledGate",
            reason="Skill enabled" if skill_enabled else "Skill disabled or missing",
            details={"enabled": skill_enabled},
        )
    )

    data_source_valid = data_source in DATA_SOURCES
    results.append(
        GateResult(
            passed=data_source_valid,
            gate_name="DataSourceValidGate",
            reason="Data source valid" if data_source_valid else "Unknown data source",
            details={"data_source": data_source},
        )
    )

    workflow_valid = workflow_type in WORKFLOW_TYPES
    results.append(
        GateResult(
            passed=workflow_valid,
            gate_name="WorkflowTypeValidGate",
            reason="Workflow type valid" if workflow_valid else "Unknown workflow type",
            details={"workflow_type": workflow_type},
        )
    )

    if agent_context is not None:
        results.extend(_run_advanced_pre_gates(skill=skill, skill_id=skill_id, agent_context=agent_context))

    return results


def _run_advanced_pre_gates(
    *,
    skill: dict[str, Any] | None,
    skill_id: str,
    agent_context: dict[str, Any],
) -> list[GateResult]:
    results: list[GateResult] = []

    cost_gate = agent_context.get("cost_gate_result")
    if cost_gate is not None:
        passed = bool(cost_gate.get("passed", True))
        results.append(
            GateResult(
                passed=passed,
                gate_name="CostGate",
                reason=str(cost_gate.get("reason", "Cost gate evaluated.")),
                details=cost_gate,
            )
        )

    trust_result = agent_context.get("trust_result")
    if trust_result is not None:
        level = trust_result.get("trust_level", "trusted")
        passed = level in {"trusted", "limited_trust"}
        results.append(
            GateResult(
                passed=passed,
                gate_name="TrustGate",
                reason="; ".join(trust_result.get("reasons", [])),
                details=trust_result,
            )
        )

    security_result = agent_context.get("security_result")
    if security_result is not None:
        passed = bool(security_result.get("passed", True))
        results.append(
            GateResult(
                passed=passed,
                gate_name="SecurityGate",
                reason=str(security_result.get("detected_issue") or "Security check passed."),
                details=security_result,
            )
        )

    if skill and _requires_human_approval(skill_id=skill_id, skill=skill, agent_context=agent_context):
        approval_passed, approval_reason, approval_details = _evaluate_human_approval(
            skill_id=skill_id,
            agent_context=agent_context,
        )
        results.append(
            GateResult(
                passed=approval_passed,
                gate_name="HumanApprovalGate",
                reason=approval_reason,
                details=approval_details,
            )
        )

    return results


def _requires_human_approval(
    *,
    skill_id: str,
    skill: dict[str, Any],
    agent_context: dict[str, Any],
) -> bool:
    if agent_context.get("approval_override"):
        return True
    if skill.get("requires_approval"):
        return True
    if skill_id in APPROVAL_REQUIRED_SKILLS:
        return True
    if agent_context.get("resume_after_failure") and skill_id == "resume_from_checkpoint":
        return True
    if agent_context.get("gate_failure_override") and skill_id == "resolve_human_approval":
        return True
    if agent_context.get("verification_failed") and skill_id in REPORT_RELEASE_SKILLS:
        return True
    return False


def _evaluate_human_approval(
    *,
    skill_id: str,
    agent_context: dict[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    approved_skills = set(agent_context.get("approved_skills") or [])
    if skill_id in approved_skills:
        return True, f"Skill '{skill_id}' pre-approved in run context.", {"approved_skills": list(approved_skills)}

    approval_id = agent_context.get("active_approval_id")
    approval_queue = agent_context.get("approval_queue")
    if approval_id and approval_queue is not None and approval_queue.is_approved(approval_id):
        return True, f"Approval '{approval_id}' is approved.", {"approval_id": approval_id}

    if agent_context.get("approval_override") and agent_context.get("override_justification"):
        return True, "Approval overridden with justification.", {
            "justification": agent_context.get("override_justification")
        }

    if agent_context.get("skip_approval_gate"):
        return True, "Approval gate skipped for demo workflow path.", {}

    return False, f"Human approval required for skill '{skill_id}'.", {
        "skill_id": skill_id,
        "approval_id": approval_id,
    }


def run_post_execution_gates(
    *,
    result: dict[str, Any] | None,
    report_path: Path | None,
    audit_event: dict[str, Any] | None,
    unhandled_exception: str | None = None,
) -> list[GateResult]:
    """Run post-execution gates after a skill executes."""
    results: list[GateResult] = []

    results.append(
        GateResult(
            passed=result is not None,
            gate_name="ResultExistsGate",
            reason="Execution result present" if result else "No execution result",
            details={"has_result": result is not None},
        )
    )

    report_required = bool(result and result.get("report_expected"))
    report_exists = report_path is not None and report_path.exists()
    if report_required:
        results.append(
            GateResult(
                passed=report_exists,
                gate_name="ReportPathExistsGate",
                reason="Report file written" if report_exists else "Report file missing",
                details={"report_path": str(report_path) if report_path else None},
            )
        )

    results.append(
        GateResult(
            passed=audit_event is not None,
            gate_name="AuditEventGeneratedGate",
            reason="Audit event generated" if audit_event else "Audit event missing",
            details={"has_audit_event": audit_event is not None},
        )
    )

    no_exception = unhandled_exception is None
    results.append(
        GateResult(
            passed=no_exception,
            gate_name="NoUnhandledExceptionGate",
            reason="No unhandled exception" if no_exception else unhandled_exception or "",
            details={"unhandled_exception": unhandled_exception},
        )
    )

    return results


def all_gates_passed(gate_results: list[GateResult]) -> bool:
    """Return True when every gate in the list passed."""
    return all(gate.passed for gate in gate_results)
