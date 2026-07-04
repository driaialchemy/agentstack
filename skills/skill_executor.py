"""Governed skill executor for Phase 2 (linear, no agents)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analytics.charting import generate_revenue_chart
from analytics.eda import run_eda as analytics_run_eda
from analytics.fourier import run_fourier_forecast as analytics_run_fourier_forecast
from analytics.regression import run_regression as analytics_run_regression
from analytics.report_builder import build_analytics_report, verify_analytics_report as verify_report
from data_sources.synthetic_data import get_monthly_time_series, get_structured_records
from data_sources.synthetic_documents import get_documents
from governance.audit_logger import log_skill_event
from governance.approval_queue import ApprovalQueue
from governance.checkpoint_manager import CheckpointManager
from governance.cost_tracker import CostTracker, DEFAULT_RUN_BUDGET
from governance.dead_letter_queue import DeadLetterQueue
from governance.demo_workflow import build_document_output, build_structured_output
from governance.gate_engine import all_gates_passed, run_post_execution_gates, run_pre_execution_gates
from governance.incident_report import IncidentReporter
from governance.policy_engine import evaluate_policy
from governance.recovery_manager import RecoveryManager
from governance.result_contract import enrich_governed_result, failure_class_for_policy
from governance.security_engine import run_security_check
from governance.trust_engine import evaluate_trust
from governance.workflow_charter import DATA_SOURCES, WORKFLOW_TYPES
from evidence.audit_evidence_report import build_audit_evidence_report
from evidence.evidence_exporter import export_evidence_bundle
from evidence.governance_run_summary import build_governance_run_summary
from evidence.policy_coverage_report import build_policy_coverage_report
from evidence.skill_coverage_report import build_skill_coverage_report
from memory.memory_validator import validate_memory_write
from memory.quarantine_store import QuarantineStore
from memory.session_store import SessionStore
from memory.working_memory import WorkingMemory
from skills.skill_registry import get_skill_by_id

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"
DEFAULT_CHARTS_DIR = REPO_ROOT / "storage" / "charts"
DEFAULT_CHECKPOINT_DIR = REPO_ROOT / "storage" / "checkpoints"
DEFAULT_DEAD_LETTER_PATH = REPO_ROOT / "storage" / "dead_letter" / "dead_letter.jsonl"
DEFAULT_QUARANTINE_PATH = REPO_ROOT / "storage" / "quarantine" / "quarantine.jsonl"
DEFAULT_WORKING_DIR = REPO_ROOT / "storage" / "memory" / "working"
DEFAULT_SESSION_DIR = REPO_ROOT / "storage" / "memory" / "session"
DEFAULT_APPROVAL_PATH = REPO_ROOT / "storage" / "approvals" / "approval_queue.jsonl"
DEFAULT_INCIDENT_DIR = REPO_ROOT / "storage" / "incidents"
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "storage" / "evidence"

PHASE6_SKILLS = {
    "evaluate_cost",
    "evaluate_trust",
    "run_security_check",
    "create_incident_report",
    "request_human_approval",
    "resolve_human_approval",
    "generate_policy_coverage_report",
    "generate_skill_coverage_report",
    "generate_audit_evidence_report",
    "generate_governance_run_summary",
}

ANALYTICS_WORKFLOW = "Structured data analytics"

WORKFLOW_SKILL_MAP = {
    "Structured data preview": "structured_data_summary",
    "Document review preview": "document_review_summary",
}


def resolve_skill_for_workflow(workflow_type: str) -> str:
    """Map a workflow type to its primary governed skill."""
    return WORKFLOW_SKILL_MAP[workflow_type]


def default_input_size(*, workflow_type: str, data_source: str) -> int:
    """Return the natural input size for a workflow (records or documents)."""
    if workflow_type in {"Structured data preview", ANALYTICS_WORKFLOW}:
        return len(get_structured_records())
    if workflow_type == "Document review preview":
        return len(get_documents())
    return 0


def _gate_status(gate_results: list) -> str:
    return "passed" if all_gates_passed(gate_results) else "failed"


def _finalize_execute_result(
    result: dict[str, Any],
    *,
    run_id: str,
    workflow_type: str,
    data_source: str,
    accountability_owner: str,
    policy_decision: str | None = None,
) -> dict[str, Any]:
    result.setdefault("run_id", run_id)
    result.setdefault("workflow_type", workflow_type)
    result.setdefault("data_source", data_source)
    result.setdefault("accountability_owner", accountability_owner)
    failure = None
    if result.get("status") != "success":
        failure = failure_class_for_policy(policy_decision) or "GOVERNANCE_FAILURE"
    return enrich_governed_result(result, failure_class=failure)


def _write_report(run_id: str, payload: dict[str, Any], reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{run_id}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


def _validate_workflow_pairing(*, workflow_type: str, data_source: str) -> None:
    if workflow_type == "Structured data preview" and data_source != "Synthetic structured database":
        raise ValueError("Structured data preview requires the synthetic structured database.")
    if workflow_type == "Document review preview" and data_source != "Synthetic document database":
        raise ValueError("Document review preview requires the synthetic document database.")
    if workflow_type == ANALYTICS_WORKFLOW and data_source != "Synthetic structured database":
        raise ValueError("Structured data analytics requires the synthetic structured database.")


def _analytics_context(agent_context: dict[str, Any] | None) -> dict[str, Any]:
    return agent_context or {}


def _resolve_path(value: Path | str | None, default: Path) -> Path:
    if value is None:
        return default
    return Path(value) if not isinstance(value, Path) else value


def _memory_stores(context: dict[str, Any]) -> dict[str, Any]:
    working_dir = _resolve_path(context.get("working_memory_dir"), DEFAULT_WORKING_DIR)
    session_dir = _resolve_path(context.get("session_memory_dir"), DEFAULT_SESSION_DIR)
    quarantine_path = _resolve_path(context.get("quarantine_path"), DEFAULT_QUARANTINE_PATH)
    checkpoint_dir = _resolve_path(context.get("checkpoint_dir"), DEFAULT_CHECKPOINT_DIR)
    dead_letter_path = _resolve_path(context.get("dead_letter_path"), DEFAULT_DEAD_LETTER_PATH)
    return {
        "working": WorkingMemory(working_dir),
        "session": SessionStore(session_dir),
        "quarantine": QuarantineStore(quarantine_path),
        "checkpoints": CheckpointManager(checkpoint_dir),
        "dead_letter": DeadLetterQueue(dead_letter_path),
        "recovery": RecoveryManager(
            checkpoint_manager=CheckpointManager(checkpoint_dir),
            quarantine_store=QuarantineStore(quarantine_path),
            dead_letter_queue=DeadLetterQueue(dead_letter_path),
        ),
    }


def _governance_stores(context: dict[str, Any]) -> dict[str, Any]:
    approval_path = _resolve_path(context.get("approval_path"), DEFAULT_APPROVAL_PATH)
    incident_dir = _resolve_path(context.get("incident_dir"), DEFAULT_INCIDENT_DIR)
    evidence_dir = _resolve_path(context.get("evidence_dir"), DEFAULT_EVIDENCE_DIR)
    return {
        "approval_queue": context.get("approval_queue") or ApprovalQueue(approval_path),
        "incident_reporter": context.get("incident_reporter") or IncidentReporter(incident_dir),
        "cost_tracker": context.get("cost_tracker") or CostTracker(
            float(context.get("run_budget", DEFAULT_RUN_BUDGET))
        ),
        "evidence_dir": evidence_dir,
    }


def _validate_governance_execution(
    *,
    run_id: str,
    accountability_owner: str,
    charter_complete: bool,
    skill_id: str,
) -> str | None:
    if skill_id not in PHASE6_SKILLS:
        return None
    if not str(run_id or "").strip():
        return "run_id is required for governance skill execution."
    if not str(accountability_owner or "").strip():
        return "Accountability owner is required for governance skill execution."
    if not charter_complete:
        return "Charter must be complete for governance skill execution."
    return None


def _execute_skill_body(
    *,
    skill_id: str,
    workflow_type: str,
    data_source: str,
    agent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the skill implementation (reuses Phase 1 demo logic)."""
    if skill_id == "intake_summary":
        if data_source not in DATA_SOURCES:
            raise ValueError(f"Unknown data source: {data_source}")
        if workflow_type not in WORKFLOW_TYPES:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        _validate_workflow_pairing(workflow_type=workflow_type, data_source=data_source)
        output = {
            "skill_id": skill_id,
            "workflow_type": workflow_type,
            "data_source": data_source,
            "intake_valid": True,
            "synthetic_only": True,
            "message": (
                f"Intake accepted for '{workflow_type}' using '{data_source}' "
                "(synthetic demo data only)."
            ),
        }
        return {"output": output, "report_expected": False}

    if skill_id == "output_verification":
        context = agent_context or {}
        analysis_result = context.get("analysis_result")
        if not analysis_result or analysis_result.get("status") != "success":
            raise ValueError("Analysis result missing or unsuccessful.")
        analysis_output = analysis_result.get("output")
        if not analysis_output:
            raise ValueError("Analysis output is empty.")
        report_path = analysis_result.get("report_path")
        if not report_path:
            raise ValueError("Expected report path is missing from analysis result.")
        policy = analysis_result.get("policy", {})
        if policy.get("policy_decision") != "allow":
            raise ValueError("Analysis policy decision was not 'allow'.")
        pre_gates = analysis_result.get("pre_gates", [])
        post_gates = analysis_result.get("post_gates", [])
        if pre_gates and not all(gate.get("passed") for gate in pre_gates):
            raise ValueError("Analysis pre-gates did not all pass.")
        if post_gates and not all(gate.get("passed") for gate in post_gates):
            raise ValueError("Analysis post-gates did not all pass.")
        output = {
            "skill_id": skill_id,
            "verified": True,
            "report_path": report_path,
            "checks_passed": [
                "analysis_output_exists",
                "report_path_exists",
                "policy_allowed",
                "pre_gates_passed",
                "post_gates_passed",
            ],
            "message": "Analysis output verified without modifying source data.",
        }
        return {"output": output, "report_expected": False}

    if skill_id == "governed_workflow_summary":
        context = agent_context or {}
        intake_output = context.get("intake_output", {})
        verification_output = context.get("verification_output", {})
        owner = context.get("accountability_owner", "unknown")
        summary_lines = [
            f"Accountability owner: {owner}.",
            f"Workflow type: {workflow_type}.",
            f"Data source: {data_source} (synthetic demo data only).",
            f"Intake: {intake_output.get('message', 'Intake step completed.')}",
            "Analysis: governed skill execution completed on synthetic data.",
            f"Verification: {verification_output.get('message', 'Verification step completed.')}",
            (
                "This is a governed demonstration workflow. "
                "It uses synthetic data and does not represent real client outcomes."
            ),
        ]
        output = {
            "skill_id": skill_id,
            "workflow_type": workflow_type,
            "data_source": data_source,
            "summary_text": " ".join(summary_lines),
            "summary_lines": summary_lines,
            "synthetic_data_notice": True,
        }
        return {"output": output, "report_expected": False}

    if skill_id == "run_eda":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("run_eda requires Structured data analytics workflow.")
        structured = get_structured_records()
        time_series = get_monthly_time_series()
        eda_output = analytics_run_eda(structured_records=structured, time_series=time_series)
        eda_output["skill_id"] = skill_id
        return {"output": eda_output, "report_expected": False}

    if skill_id == "run_regression":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("run_regression requires Structured data analytics workflow.")
        regression_output = analytics_run_regression(time_series=get_monthly_time_series())
        regression_output["skill_id"] = skill_id
        return {"output": regression_output, "report_expected": False}

    if skill_id == "run_fourier_forecast":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("run_fourier_forecast requires Structured data analytics workflow.")
        forecast_output = analytics_run_fourier_forecast(time_series=get_monthly_time_series())
        forecast_output["skill_id"] = skill_id
        return {"output": forecast_output, "report_expected": False}

    if skill_id == "generate_chart":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("generate_chart requires Structured data analytics workflow.")
        context = _analytics_context(agent_context)
        forecast = context.get("forecast_result", {})
        projected = forecast.get("projected_values")
        run_id = context.get("run_id", "chart")
        chart_path = DEFAULT_CHARTS_DIR / f"{run_id}_revenue.png"
        chart_output = generate_revenue_chart(
            time_series=get_monthly_time_series(),
            output_path=chart_path,
            forecast=projected,
        )
        chart_output["skill_id"] = skill_id
        return {"output": chart_output, "report_expected": False}

    if skill_id == "generate_analytics_report":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("generate_analytics_report requires Structured data analytics workflow.")
        context = _analytics_context(agent_context)
        required_keys = ("eda_result", "regression_result", "forecast_result", "chart_result")
        missing = [key for key in required_keys if key not in context]
        if missing:
            raise ValueError(f"Missing analytics context for report: {', '.join(missing)}")
        report = build_analytics_report(
            run_id=context["run_id"],
            accountability_owner=context["accountability_owner"],
            workflow_type=workflow_type,
            data_source=data_source,
            eda=context["eda_result"],
            regression=context["regression_result"],
            forecast=context["forecast_result"],
            chart=context["chart_result"],
            reports_dir=DEFAULT_REPORTS_DIR,
        )
        report["skill_id"] = skill_id
        return {"output": report, "report_expected": True}

    if skill_id == "verify_analytics_report":
        if workflow_type != ANALYTICS_WORKFLOW:
            raise ValueError("verify_analytics_report requires Structured data analytics workflow.")
        context = _analytics_context(agent_context)
        report = context.get("analytics_report")
        verification = verify_report(report)
        if not verification.get("verified"):
            raise ValueError(verification.get("message", "Analytics report verification failed."))
        output = {
            "skill_id": skill_id,
            "verified": True,
            "message": verification["message"],
            "checks_passed": verification.get("checks_passed", []),
        }
        return {"output": output, "report_expected": False}

    if skill_id == "structured_data_summary":
        output = build_structured_output(workflow_type=workflow_type, data_source=data_source)
        output["skill_id"] = skill_id
        return {"output": output, "report_expected": True}

    if skill_id == "document_review_summary":
        output = build_document_output(workflow_type=workflow_type, data_source=data_source)
        output["skill_id"] = skill_id
        return {"output": output, "report_expected": True}

    if skill_id == "report_writer":
        if workflow_type == "Structured data preview":
            output = build_structured_output(workflow_type=workflow_type, data_source=data_source)
        elif workflow_type == "Document review preview":
            output = build_document_output(workflow_type=workflow_type, data_source=data_source)
        else:
            raise ValueError(f"Unsupported workflow type for report_writer: {workflow_type}")
        output["skill_id"] = skill_id
        output["report_artifact"] = True
        return {"output": output, "report_expected": True}

    if skill_id == "approval_required_demo":
        raise ValueError("Approval-required skill cannot execute in Phase 2.")

    if skill_id == "disabled_demo_skill":
        raise ValueError("Disabled skill cannot execute.")

    if skill_id == "write_working_memory":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        payload = context.get("memory_payload")
        if not isinstance(payload, dict):
            raise ValueError("memory_payload is required for write_working_memory.")
        valid, reason, failure_class = validate_memory_write(payload, context)
        if not valid:
            quarantine_entry = stores["quarantine"].add(
                run_id=str(context.get("run_id", "")),
                payload=payload,
                reason=reason,
                failure_class=failure_class,
                accountability_owner=str(context.get("accountability_owner", "")),
            )
            output = {
                "skill_id": skill_id,
                "written": False,
                "quarantined": True,
                "reason": reason,
                "failure_class": failure_class,
                "quarantine_id": quarantine_entry.get("quarantine_id"),
            }
            return {"output": output, "report_expected": False}
        record = stores["working"].write(str(context["run_id"]), payload)
        return {
            "output": {
                "skill_id": skill_id,
                "written": True,
                "quarantined": False,
                "run_id": context["run_id"],
                "record": record,
            },
            "report_expected": False,
        }

    if skill_id == "write_session_memory":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        session_state = context.get("session_state")
        if not isinstance(session_state, dict):
            raise ValueError("session_state is required for write_session_memory.")
        payload = {
            **session_state,
            "run_id": context.get("run_id"),
            "accountability_owner": context.get("accountability_owner"),
            "workflow_type": context.get("workflow_type"),
            "data_source": context.get("data_source"),
            "structured": True,
            "status": session_state.get("status", "success"),
            "verified": session_state.get("verified", True),
        }
        valid, reason, failure_class = validate_memory_write(payload, context)
        if not valid:
            quarantine_entry = stores["quarantine"].add(
                run_id=str(context.get("run_id", "")),
                payload=payload,
                reason=reason,
                failure_class=failure_class,
                accountability_owner=str(context.get("accountability_owner", "")),
            )
            return {
                "output": {
                    "skill_id": skill_id,
                    "written": False,
                    "quarantined": True,
                    "reason": reason,
                    "quarantine_id": quarantine_entry.get("quarantine_id"),
                },
                "report_expected": False,
            }
        record = stores["session"].write(str(context["run_id"]), session_state)
        return {
            "output": {"skill_id": skill_id, "written": True, "record": record},
            "report_expected": False,
        }

    if skill_id == "quarantine_output":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        payload = context.get("quarantine_payload")
        reason = str(context.get("quarantine_reason") or "Output quarantined.")
        failure_class = str(context.get("failure_class") or "QUARANTINE_FAILURE")
        if not isinstance(payload, dict):
            raise ValueError("quarantine_payload is required.")
        entry = stores["quarantine"].add(
            run_id=str(context.get("run_id", "")),
            payload=payload,
            reason=reason,
            failure_class=failure_class,
            accountability_owner=str(context.get("accountability_owner", "")),
        )
        return {
            "output": {
                "skill_id": skill_id,
                "quarantine_id": entry.get("quarantine_id"),
                "reason": reason,
                "failure_class": failure_class,
            },
            "report_expected": False,
        }

    if skill_id == "create_checkpoint":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        owner = str(context.get("accountability_owner") or "").strip()
        if not owner:
            raise ValueError("Accountability owner is required for checkpoint creation.")
        if not context.get("charter_complete"):
            raise ValueError("Charter must be complete to create a checkpoint.")
        checkpoint = stores["checkpoints"].create(
            run_id=str(context["run_id"]),
            workflow_type=workflow_type,
            data_source=data_source,
            accountability_owner=owner,
            current_step=str(context.get("checkpoint_step") or "unknown"),
            completed_steps=list(context.get("completed_steps") or []),
            failed_steps=list(context.get("failed_steps") or []),
            agent_context={
                key: context.get(key)
                for key in (
                    "run_id",
                    "workflow_type",
                    "data_source",
                    "report_path",
                    "analytics_verified",
                )
            },
            output_refs=dict(context.get("output_refs") or {}),
            status="created",
        )
        return {"output": {**checkpoint, "skill_id": skill_id}, "report_expected": False}

    if skill_id == "resume_from_checkpoint":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        checkpoint_id = context.get("checkpoint_id")
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required to resume.")
        checkpoint = stores["checkpoints"].load(str(checkpoint_id))
        if checkpoint is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")
        resumed = stores["recovery"].resume_state(checkpoint)
        resumed["skill_id"] = skill_id
        return {"output": resumed, "report_expected": False}

    if skill_id == "rollback_to_checkpoint":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        checkpoint_id = context.get("checkpoint_id")
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required to roll back.")
        checkpoint = stores["checkpoints"].load(str(checkpoint_id))
        if checkpoint is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")
        rolled_back = stores["recovery"].rollback_state(checkpoint)
        rolled_back["skill_id"] = skill_id
        return {"output": rolled_back, "report_expected": False}

    if skill_id == "write_dead_letter":
        context = _analytics_context(agent_context)
        stores = _memory_stores(context)
        metadata = context.get("dead_letter_metadata")
        if not isinstance(metadata, dict):
            raise ValueError("dead_letter_metadata is required.")
        entry = stores["dead_letter"].append(
            run_id=str(metadata.get("run_id") or context.get("run_id")),
            task_id=str(metadata.get("task_id") or "unknown"),
            agent_id=str(metadata.get("agent_id") or "unknown"),
            skill_id=str(metadata.get("skill_id") or "unknown"),
            failure_class=str(metadata.get("failure_class") or "CASCADE_FAILURE"),
            reason=str(metadata.get("reason") or "Unrecoverable failure."),
            accountability_owner=str(context.get("accountability_owner") or ""),
            payload=metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {},
        )
        return {"output": {**entry, "skill_id": skill_id}, "report_expected": False}

    if skill_id == "evaluate_cost":
        context = _analytics_context(agent_context)
        stores = _governance_stores(context)
        tracker: CostTracker = stores["cost_tracker"]
        target_skill = str(context.get("cost_skill_id") or context.get("skill_id") or "unknown")
        gate = tracker.evaluate_skill_call(
            run_id=str(context["run_id"]),
            skill_id=target_skill,
            registry_path=context.get("registry_path"),
        )
        context["cost_gate_result"] = gate.to_dict()
        context["cost_summary"] = tracker.summary(str(context["run_id"]))
        return {
            "output": {
                "skill_id": skill_id,
                **gate.to_dict(),
                "cost_summary": context["cost_summary"],
            },
            "report_expected": False,
        }

    if skill_id == "evaluate_trust":
        context = _analytics_context(agent_context)
        result = evaluate_trust(
            agent_id=context.get("trust_agent_id") or context.get("agent_id"),
            skill_id=context.get("trust_skill_id") or context.get("skill_id"),
            data_source=context.get("data_source"),
            report_verified=context.get("analytics_verified"),
            quarantine_count=int(context.get("quarantine_count") or 0),
            security_flags=context.get("security_flags"),
            run_failures=context.get("run_failures"),
        )
        context["trust_result"] = result
        context["trust_summary"] = result
        return {"output": {"skill_id": skill_id, **result}, "report_expected": False}

    if skill_id == "run_security_check":
        context = _analytics_context(agent_context)
        payload = context.get("security_payload")
        result = run_security_check(
            content=payload if payload is not None else context.get("security_content", ""),
            source_marker=context.get("security_source_marker"),
            tool_request=context.get("security_tool_request"),
        )
        context["security_result"] = result
        context["security_summary"] = result
        return {"output": {"skill_id": skill_id, **result}, "report_expected": False}

    if skill_id == "create_incident_report":
        context = _analytics_context(agent_context)
        stores = _governance_stores(context)
        metadata = context.get("incident_metadata") or {}
        report = stores["incident_reporter"].create(
            run_id=str(context["run_id"]),
            failure_class=str(metadata.get("failure_class") or "GOVERNANCE_FAILURE"),
            triggering_agent=str(metadata.get("triggering_agent") or context.get("agent_id") or "unknown"),
            triggering_skill=str(metadata.get("triggering_skill") or context.get("skill_id") or "unknown"),
            policy_decision=str(metadata.get("policy_decision") or "unknown"),
            gate_result=metadata.get("gate_result"),
            security_result=metadata.get("security_result") or context.get("security_result"),
            recovery_action=str(metadata.get("recovery_action") or "halt"),
            accountability_owner=str(context.get("accountability_owner") or ""),
            recommended_next_action=metadata.get("recommended_next_action"),
        )
        incidents = list(context.get("incidents") or [])
        incidents.append(report)
        context["incidents"] = incidents
        return {"output": {"skill_id": skill_id, **report}, "report_expected": False}

    if skill_id == "request_human_approval":
        context = _analytics_context(agent_context)
        stores = _governance_stores(context)
        metadata = context.get("approval_request") or {}
        entry = stores["approval_queue"].request(
            run_id=str(context["run_id"]),
            requested_by_agent=str(metadata.get("requested_by_agent") or context.get("agent_id") or "governance_agent"),
            skill_id=str(metadata.get("skill_id") or context.get("skill_id") or "unknown"),
            risk_tier=str(metadata.get("risk_tier") or "high"),
            reason=str(metadata.get("reason") or "Human approval required."),
            accountability_owner=str(context.get("accountability_owner") or ""),
        )
        records = list(context.get("approval_records") or [])
        records.append(entry)
        context["approval_records"] = records
        context["active_approval_id"] = entry["approval_id"]
        return {"output": {"skill_id": skill_id, **entry}, "report_expected": False}

    if skill_id == "resolve_human_approval":
        context = _analytics_context(agent_context)
        stores = _governance_stores(context)
        metadata = context.get("approval_resolution") or {}
        approval_id = str(metadata.get("approval_id") or context.get("active_approval_id") or "")
        status = str(metadata.get("status") or "approved")
        justification = str(metadata.get("justification") or "")
        resolved = stores["approval_queue"].resolve(
            approval_id=approval_id,
            status=status,
            justification=justification,
        )
        if resolved is None:
            raise ValueError(f"Approval '{approval_id}' not found.")
        records = list(context.get("approval_records") or [])
        records.append(resolved)
        context["approval_records"] = records
        if status in {"approved", "overridden"}:
            approved = set(context.get("approved_skills") or [])
            approved.add(str(resolved.get("skill_id")))
            context["approved_skills"] = sorted(approved)
        return {"output": {"skill_id": skill_id, **resolved}, "report_expected": False}

    run_context = None
    if skill_id == "generate_policy_coverage_report":
        context = _analytics_context(agent_context)
        run_context = context.get("run_context") or context
        report = build_policy_coverage_report(run_context=run_context)
        return {"output": {"skill_id": skill_id, **report}, "report_expected": False}

    if skill_id == "generate_skill_coverage_report":
        context = _analytics_context(agent_context)
        run_context = context.get("run_context") or context
        report = build_skill_coverage_report(
            run_context=run_context,
            registry_path=context.get("registry_path"),
        )
        return {"output": {"skill_id": skill_id, **report}, "report_expected": False}

    if skill_id == "generate_audit_evidence_report":
        context = _analytics_context(agent_context)
        run_context = context.get("run_context") or context
        log_path_value = context.get("log_path")
        log_path = _resolve_path(log_path_value, REPO_ROOT / "storage" / "audit_log.jsonl") if log_path_value else None
        report = build_audit_evidence_report(
            run_id=str(context["run_id"]),
            run_context=run_context,
            log_path=log_path,
        )
        return {"output": {"skill_id": skill_id, **report}, "report_expected": False}

    if skill_id == "generate_governance_run_summary":
        context = _analytics_context(agent_context)
        run_context = dict(context.get("run_context") or context)
        run_context.setdefault("run_id", context.get("run_id"))
        run_context.setdefault("accountability_owner", context.get("accountability_owner"))
        run_context.setdefault("cost_summary", context.get("cost_summary"))
        run_context.setdefault("trust_summary", context.get("trust_summary"))
        run_context.setdefault("security_summary", context.get("security_summary"))
        summary = build_governance_run_summary(run_context=run_context)
        stores = _governance_stores(context)
        bundle = {
            "policy_coverage": build_policy_coverage_report(run_context=run_context),
            "skill_coverage": build_skill_coverage_report(run_context=run_context),
            "audit_evidence": build_audit_evidence_report(
                run_id=str(context["run_id"]),
                run_context=run_context,
                log_path=_resolve_path(context.get("log_path"), REPO_ROOT / "storage" / "audit_log.jsonl")
                if context.get("log_path")
                else None,
            ),
            "governance_run_summary": summary,
        }
        export_paths = export_evidence_bundle(
            run_id=str(context["run_id"]),
            reports=bundle,
            output_dir=stores["evidence_dir"],
        )
        context["evidence_bundle"] = bundle
        context["evidence_export_paths"] = export_paths
        context["governance_summary"] = summary
        return {
            "output": {
                "skill_id": skill_id,
                **summary,
                "export_paths": export_paths,
            },
            "report_expected": False,
        }

    raise ValueError(f"Unsupported skill: {skill_id}")


def execute_skill(
    *,
    run_id: str,
    skill_id: str,
    workflow_type: str,
    data_source: str,
    charter_complete: bool,
    accountability_owner: str,
    input_size: int | None = None,
    agent_context: dict[str, Any] | None = None,
    reports_dir: Path | None = None,
    registry_path: Path | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """
    Execute one governed skill through policy, gates, and audit logging.

    Linear execution only — no agents, no orchestrator.
    """
    events: list[dict[str, Any]] = []
    target_reports = reports_dir or DEFAULT_REPORTS_DIR
    resolved_input_size = (
        input_size
        if input_size is not None
        else default_input_size(workflow_type=workflow_type, data_source=data_source)
    )

    resolved_context = dict(agent_context or {})
    resolved_context["accountability_owner"] = accountability_owner
    resolved_context.setdefault("charter_complete", charter_complete)
    resolved_context.setdefault("run_id", run_id)
    resolved_context.setdefault("skip_approval_gate", True)

    governance_error = _validate_governance_execution(
        run_id=run_id,
        accountability_owner=accountability_owner,
        charter_complete=charter_complete,
        skill_id=skill_id,
    )
    if governance_error:
        return _finalize_execute_result(
            {
                "status": "denied",
                "skill_id": skill_id,
                "reason": governance_error,
                "policy": {},
                "pre_gates": [],
                "post_gates": [],
                "events": [],
            },
            run_id=run_id,
            workflow_type=workflow_type,
            data_source=data_source,
            accountability_owner=accountability_owner,
            policy_decision="deny_charter_incomplete",
        )

    if resolved_context.get("enable_cost_governance"):
        stores = _governance_stores(resolved_context)
        gate = stores["cost_tracker"].evaluate_skill_call(
            run_id=run_id,
            skill_id=skill_id,
            registry_path=registry_path,
        )
        resolved_context["cost_gate_result"] = gate.to_dict()

    policy = evaluate_policy(
        skill_id=skill_id,
        charter_complete=charter_complete,
        data_source=data_source,
        workflow_type=workflow_type,
        input_size=resolved_input_size,
        registry_path=registry_path,
        approved_skills=list(resolved_context.get("approved_skills") or []),
    )

    pre_gates = run_pre_execution_gates(
        skill_id=skill_id,
        charter_complete=charter_complete,
        policy=policy,
        data_source=data_source,
        workflow_type=workflow_type,
        registry_path=registry_path,
        agent_context=resolved_context,
    )
    pre_status = _gate_status(pre_gates)

    if not policy.allowed or not all_gates_passed(pre_gates):
        denial_reason = policy.reason
        if not all_gates_passed(pre_gates):
            failed = next(g for g in pre_gates if not g.passed)
            denial_reason = failed.reason

        event = log_skill_event(
            run_id=run_id,
            accountability_owner=accountability_owner,
            skill_id=skill_id,
            workflow_type=workflow_type,
            data_source=data_source,
            policy_decision=policy.policy_decision,
            pre_gate_status=pre_status,
            post_gate_status="skipped",
            action="skill_denied",
            status="denied",
            summary=denial_reason,
            log_path=log_path,
            registry_path=registry_path,
            failure_class=failure_class_for_policy(policy.policy_decision),
        )
        events.append(event)
        return _finalize_execute_result(
            {
                "status": "denied",
                "skill_id": skill_id,
                "reason": denial_reason,
                "policy": policy.to_dict(),
                "pre_gates": [gate.to_dict() for gate in pre_gates],
                "post_gates": [],
                "events": events,
            },
            run_id=run_id,
            workflow_type=workflow_type,
            data_source=data_source,
            accountability_owner=accountability_owner,
            policy_decision=policy.policy_decision,
        )

    execution_result: dict[str, Any] | None = None
    report_path: Path | None = None
    audit_event: dict[str, Any] | None = None
    unhandled_exception: str | None = None
    output: dict[str, Any] | None = None

    resolved_context.setdefault("log_path", str(log_path) if log_path else None)

    try:
        execution_result = _execute_skill_body(
            skill_id=skill_id,
            workflow_type=workflow_type,
            data_source=data_source,
            agent_context=resolved_context,
        )
        output = execution_result["output"]
        if execution_result.get("report_expected"):
            report_path = _write_report(run_id, output, target_reports)

        audit_event = log_skill_event(
            run_id=run_id,
            accountability_owner=accountability_owner,
            skill_id=skill_id,
            workflow_type=workflow_type,
            data_source=data_source,
            policy_decision=policy.policy_decision,
            pre_gate_status=pre_status,
            post_gate_status="pending",
            action="skill_executed",
            status="success",
            summary=f"Skill '{skill_id}' executed successfully.",
            log_path=log_path,
        )
        events.append(audit_event)

        if resolved_context.get("cost_tracker") or resolved_context.get("enable_cost_governance"):
            stores = _governance_stores(resolved_context)
            cost_entry = stores["cost_tracker"].record_skill_call(
                run_id=run_id,
                skill_id=skill_id,
                registry_path=registry_path,
            )
            log_skill_event(
                run_id=run_id,
                accountability_owner=accountability_owner,
                skill_id=skill_id,
                workflow_type=workflow_type,
                data_source=data_source,
                policy_decision=policy.policy_decision,
                pre_gate_status=pre_status,
                post_gate_status="passed",
                action="cost_recorded",
                status="success",
                summary=(
                    f"Estimated cost {cost_entry['estimated_cost']:.2f} recorded "
                    f"(run total {cost_entry['run_total_cost']:.2f})."
                ),
                log_path=log_path,
            )

    except Exception as exc:
        unhandled_exception = str(exc)
        audit_event = log_skill_event(
            run_id=run_id,
            accountability_owner=accountability_owner,
            skill_id=skill_id,
            workflow_type=workflow_type,
            data_source=data_source,
            policy_decision=policy.policy_decision,
            pre_gate_status=pre_status,
            post_gate_status="failed",
            action="skill_failed",
            status="error",
            summary=f"Skill '{skill_id}' failed: {exc}",
            log_path=log_path,
            registry_path=registry_path,
            failure_class="SKILL_FAILURE",
        )
        events.append(audit_event)
        return _finalize_execute_result(
            {
                "status": "error",
                "skill_id": skill_id,
                "error": unhandled_exception,
                "policy": policy.to_dict(),
                "pre_gates": [gate.to_dict() for gate in pre_gates],
                "post_gates": [],
                "events": events,
            },
            run_id=run_id,
            workflow_type=workflow_type,
            data_source=data_source,
            accountability_owner=accountability_owner,
            policy_decision=policy.policy_decision,
        )

    post_gates = run_post_execution_gates(
        result=execution_result,
        report_path=report_path,
        audit_event=audit_event,
        unhandled_exception=unhandled_exception,
    )
    post_status = _gate_status(post_gates)

    if audit_event is not None:
        audit_event["post_gate_status"] = post_status

    completion_event = log_skill_event(
        run_id=run_id,
        accountability_owner=accountability_owner,
        skill_id=skill_id,
        workflow_type=workflow_type,
        data_source=data_source,
        policy_decision=policy.policy_decision,
        pre_gate_status=pre_status,
        post_gate_status=post_status,
        action="skill_completed",
        status="success" if all_gates_passed(post_gates) else "warning",
        summary=(
            f"Skill '{skill_id}' post-execution gates "
            f"{'passed' if all_gates_passed(post_gates) else 'failed'}."
        ),
        log_path=log_path,
    )
    events.append(completion_event)

    if not all_gates_passed(post_gates):
        failed = next(g for g in post_gates if not g.passed)
        return _finalize_execute_result(
            {
                "status": "error",
                "skill_id": skill_id,
                "error": failed.reason,
                "policy": policy.to_dict(),
                "pre_gates": [gate.to_dict() for gate in pre_gates],
                "post_gates": [gate.to_dict() for gate in post_gates],
                "output": output,
                "report_path": str(report_path) if report_path else None,
                "events": events,
            },
            run_id=run_id,
            workflow_type=workflow_type,
            data_source=data_source,
            accountability_owner=accountability_owner,
            policy_decision=policy.policy_decision,
        )

    return _finalize_execute_result(
        {
            "status": "success",
            "skill_id": skill_id,
            "policy": policy.to_dict(),
            "pre_gates": [gate.to_dict() for gate in pre_gates],
            "post_gates": [gate.to_dict() for gate in post_gates],
            "output": output,
            "report_path": str(report_path) if report_path else None,
            "events": events,
        },
        run_id=run_id,
        workflow_type=workflow_type,
        data_source=data_source,
        accountability_owner=accountability_owner,
        policy_decision=policy.policy_decision,
    )
