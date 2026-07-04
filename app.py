"""agentstack — governed intelligence stack (Phase 1–6)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from agents.agent_registry import get_all_agents, get_enabled_agents
from governance.audit_logger import generate_run_id, read_audit_events
from governance.failure_taxonomy import recommended_action
from governance.workflow_charter import (
    CHARTER_RULE,
    DATA_SOURCES,
    REQUIRED_CHARTER_FIELDS,
    WORKFLOW_TYPES,
    charter_status_message,
    load_charter_text,
    validate_charter,
)
from orchestration.linear_orchestrator import (
    ANALYTICS_STEP_SEQUENCE,
    DEFAULT_AGENT_SEQUENCE,
    LinearAgentOrchestrator,
)
from skills.skill_executor import (
    ANALYTICS_WORKFLOW,
    execute_skill,
    resolve_skill_for_workflow,
)
from skills.skill_registry import get_all_skills, get_enabled_skills

REPO_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "reports"
ORCHESTRATOR = LinearAgentOrchestrator(reports_dir=REPORTS_DIR)

st.set_page_config(
    page_title="agentstack — Governed Demo",
    page_icon="🛡️",
    layout="wide",
)

st.title("agentstack")
st.caption("Phases 1–6 complete — governed multi-agent demo stack")
st.info(f"**Governance rule:** {CHARTER_RULE}")

DEMO_SECTIONS = [
    "Workflow Charter",
    "Run Workflow",
    "Output",
    "Analytics & Reporting",
    "Memory & Recovery",
    "Advanced Governance & Evidence",
    "Skills Governance (Failure Demos)",
    "Agents & Orchestration (Failure Demos)",
    "Audit / Evidence Viewer",
]

with st.sidebar:
    st.markdown("### Demo map")
    for section in DEMO_SECTIONS:
        st.markdown(f"- {section}")
    st.caption("Use the tabs above to walk through each governed area.")

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_run_id" not in st.session_state:
    st.session_state.last_run_id = None
if "last_governance" not in st.session_state:
    st.session_state.last_governance = None
if "last_orchestration" not in st.session_state:
    st.session_state.last_orchestration = None
if "last_memory_demo" not in st.session_state:
    st.session_state.last_memory_demo = None


def _render_blocked_state(result: dict[str, Any]) -> None:
    """Show a consistent blocked/denied/error message with governance context."""
    status = result.get("status", "unknown")
    message = result.get("message") or result.get("reason") or result.get("error") or "Blocked."
    if status == "denied":
        st.warning(message)
    elif status == "error":
        st.error(message)
    else:
        st.info(message)

    failure_class = result.get("failure_class")
    if failure_class:
        st.write(
            f"Failure class: `{failure_class}` → "
            f"recommended action: `{result.get('recommended_action') or recommended_action(failure_class)}`"
        )
    if result.get("errors"):
        with st.expander("Blocked details"):
            for item in result["errors"]:
                st.write(f"- {item}")


def _ensure_charter_state() -> None:
    """Initialize charter widget keys so validation reads stable session state."""
    for field_name, _ in REQUIRED_CHARTER_FIELDS:
        if field_name not in st.session_state:
            st.session_state[field_name] = (
                "" if field_name == "accountability_owner" else False
            )


def _render_charter_checklist() -> dict[str, Any]:
    """Render required charter acknowledgments using validator field names."""
    _ensure_charter_state()
    col1, col2 = st.columns(2)
    with col1:
        form_data = {
            "business_problem_ack": st.checkbox(
                "Business problem acknowledged",
                key="business_problem_ack",
            ),
            "desired_outcome_ack": st.checkbox(
                "Desired outcome acknowledged",
                key="desired_outcome_ack",
            ),
            "accountability_owner": st.text_input(
                "Accountability owner",
                placeholder="e.g. Demo Operator",
                key="accountability_owner",
            ),
        }
    with col2:
        form_data["workflow_scope_ack"] = st.checkbox(
            "Workflow scope confirmed (Phase 1–6 demo only)",
            key="workflow_scope_ack",
        )
        form_data["out_of_scope_ack"] = st.checkbox(
            "Out-of-scope activities excluded (no Phase 7+ features)",
            key="out_of_scope_ack",
        )
        form_data["audit_enabled_ack"] = st.checkbox(
            "Audit and observability enabled",
            key="audit_enabled_ack",
        )
    return form_data


def _charter_form_data() -> dict[str, Any]:
    _ensure_charter_state()
    form_data: dict[str, Any] = {}
    for field_name, _ in REQUIRED_CHARTER_FIELDS:
        if field_name == "accountability_owner":
            form_data[field_name] = str(st.session_state.get(field_name, "") or "")
        else:
            form_data[field_name] = bool(st.session_state.get(field_name, False))
    return form_data


def _render_charter_status(form_data: dict[str, Any]) -> tuple[bool, list[str]]:
    is_complete, missing = validate_charter(form_data)
    message = charter_status_message(is_complete, missing)
    if is_complete:
        st.success(message)
    else:
        st.warning(message)
    return is_complete, missing


def _run_governed_skill(
    *,
    skill_id: str,
    workflow_type: str,
    data_source: str,
    charter_complete: bool,
    accountability_owner: str,
    input_size: int | None = None,
) -> dict[str, Any]:
    run_id = generate_run_id()
    result = execute_skill(
        run_id=run_id,
        skill_id=skill_id,
        workflow_type=workflow_type,
        data_source=data_source,
        charter_complete=charter_complete,
        accountability_owner=accountability_owner,
        input_size=input_size,
        reports_dir=REPORTS_DIR,
    )
    result["run_id"] = run_id
    return result


def _run_orchestrated_workflow(
    *,
    workflow_type: str,
    data_source: str,
    charter_complete: bool,
    accountability_owner: str,
    agent_sequence: list[str] | None = None,
    skill_overrides: dict[str, str] | None = None,
    enable_governance_evidence: bool = True,
) -> dict[str, Any]:
    return ORCHESTRATOR.run(
        workflow_type=workflow_type,
        data_source=data_source,
        charter_complete=charter_complete,
        accountability_owner=accountability_owner,
        agent_sequence=agent_sequence,
        skill_overrides=skill_overrides,
        enable_governance_evidence=enable_governance_evidence,
    )


def _render_analysis_output(output: dict[str, Any]) -> None:
    summary = output.get("summary", {})

    if output.get("workflow_type") == "Structured data preview":
        col1, col2, col3 = st.columns(3)
        col1.metric("Records", summary.get("record_count", 0))
        col2.metric("Total revenue (USD)", summary.get("total_revenue_usd", 0))
        col3.metric("Average revenue (USD)", summary.get("average_revenue_usd", 0))
        st.write("Regions:", ", ".join(summary.get("regions", [])))
        st.write("Categories:", ", ".join(summary.get("categories", [])))
        st.dataframe(output.get("records", []), use_container_width=True)
    elif output.get("workflow_type") == "Document review preview":
        col1, col2 = st.columns(2)
        col1.metric("Documents", summary.get("document_count", 0))
        col2.metric("Risk tiers", len(summary.get("risk_counts", {})))
        st.write("Document types:", ", ".join(summary.get("doc_types", [])))
        st.write("Risk counts:", summary.get("risk_counts", {}))
        st.dataframe(output.get("documents", []), use_container_width=True)


def _render_output(result: dict[str, Any]) -> None:
    if result.get("analytics_results"):
        analytics = result["analytics_results"]
        st.markdown("### EDA summary")
        st.write(analytics.get("eda", {}).get("interpretation", ""))
        st.json(analytics.get("eda", {}))

        st.markdown("### Regression result")
        regression = analytics.get("regression", {})
        st.write(regression.get("interpretation", ""))
        st.write("R-squared:", regression.get("r_squared"))
        st.write("Limitations:", regression.get("limitations", []))

        st.markdown("### Forecast result")
        forecast = analytics.get("forecast", {})
        st.write(forecast.get("interpretation", ""))
        st.warning(forecast.get("limitation_note", ""))
        st.json(forecast.get("projected_values", []))

        chart = analytics.get("chart", {})
        chart_path = chart.get("chart_path")
        if chart_path and Path(chart_path).exists():
            st.markdown("### Generated chart")
            st.image(chart_path)

        report = result.get("analytics_report") or {}
        if report:
            st.markdown("### Report preview")
            md_path = report.get("markdown_path")
            if md_path and Path(md_path).exists():
                st.markdown(Path(md_path).read_text(encoding="utf-8"))
            st.write("Verification status:", "Verified" if result.get("analytics_verified") else "Not verified")

        st.markdown("### Governance evidence")
        st.write(f"Accountability owner: `{result.get('accountability_owner')}`")
        st.write(f"Report path: `{result.get('report_path')}`")
        with st.expander("Raw orchestration JSON"):
            st.json(result)
        return

    if result.get("analysis_output"):
        _render_analysis_output(result["analysis_output"])
        if result.get("final_summary"):
            st.markdown("**Governed workflow summary**")
            st.write(result["final_summary"].get("summary_text", ""))
        with st.expander("Raw orchestration JSON"):
            st.json(result)
        return

    output = result.get("output") or {}
    if output:
        _render_analysis_output(output)
    with st.expander("Raw JSON output"):
        st.json(output if output else result)


st.subheader("Run charter checklist")
st.caption(f"**{CHARTER_RULE}** Complete every item before running workflows.")
charter_form = _render_charter_checklist()
charter_is_complete, charter_missing = _render_charter_status(charter_form)

tab_charter, tab_run, tab_output, tab_analytics, tab_memory, tab_advanced, tab_governance, tab_agents, tab_audit = st.tabs(
    [
        "Workflow Charter",
        "Run Workflow",
        "Output",
        "Analytics & Reporting",
        "Memory & Recovery",
        "Advanced Governance & Evidence",
        "Skills Governance",
        "Agents & Orchestration",
        "Audit Log",
    ],
    key="main_demo_tabs",
)

with tab_charter:
    st.subheader("Agent Charter")
    st.markdown(
        "Complete the checklist above before running a workflow. "
        f"**{CHARTER_RULE}**"
    )

    with st.expander("View full AGENT_CHARTER.md", expanded=False):
        try:
            st.markdown(load_charter_text())
        except RuntimeError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Charter checklist status")
    _render_charter_status(_charter_form_data())

with tab_run:
    st.subheader("Run demonstration workflow")
    st.caption(
        "Workflows run through the linear agent orchestrator. "
        "Each agent step calls the governed skill executor."
    )

    data_source = st.selectbox(
        "Data source",
        options=DATA_SOURCES,
        help="Phase 1–3 supports synthetic sources only.",
    )
    workflow_type = st.selectbox(
        "Workflow type",
        options=WORKFLOW_TYPES,
        help="Choose a workflow that matches your selected data source.",
    )

    selected_skill = (
        "run_eda → run_regression → run_fourier_forecast → generate_chart"
        if workflow_type == ANALYTICS_WORKFLOW
        else resolve_skill_for_workflow(workflow_type)
    )
    st.write(f"**Primary analysis path:** `{selected_skill}`")
    if workflow_type == ANALYTICS_WORKFLOW:
        sequence_text = " → ".join(
            f"{agent}[{skill}]" if skill else agent
            for agent, skill in ANALYTICS_STEP_SEQUENCE
        )
        st.write("**Agent sequence:**", sequence_text)
    else:
        st.write("**Agent sequence:**", " → ".join(f"`{agent}`" for agent in DEFAULT_AGENT_SEQUENCE))

    st.caption("Workflow pairing guide")
    st.markdown(
        "- **Structured data preview** → Synthetic structured database\n"
        "- **Document review preview** → Synthetic document database\n"
        "- **Structured data analytics** → Synthetic structured database"
    )

    if not charter_is_complete:
        st.warning(charter_status_message(charter_is_complete, charter_missing))

    if st.button("Run workflow", type="primary"):
        form_data = _charter_form_data()
        is_complete, missing = validate_charter(form_data)

        if not is_complete:
            st.error(charter_status_message(is_complete, missing))
            st.stop()

        owner = str(form_data["accountability_owner"]).strip()
        if not owner:
            st.error(charter_status_message(False, ["Accountability owner named"]))
            st.stop()

        with st.spinner("Running governed agent workflow..."):
            result = _run_orchestrated_workflow(
                workflow_type=workflow_type,
                data_source=data_source,
                charter_complete=is_complete,
                accountability_owner=owner,
            )

        st.session_state.last_run_id = result["run_id"]
        st.session_state.last_result = result
        st.session_state.last_orchestration = result
        analysis_step = next(
            (step for step in result.get("agent_steps", []) if step.get("agent_id") == "analysis_agent"),
            None,
        )
        if analysis_step and analysis_step.get("skill_result"):
            st.session_state.last_governance = analysis_step["skill_result"]

        if result["status"] == "success":
            st.success(
                f"Orchestration completed. Report: "
                f"`{Path(result.get('report_path', '')).name}`"
            )
        elif result["status"] == "denied":
            st.warning(result.get("reason", "Workflow denied."))
        else:
            st.error(result.get("reason") or result.get("error", "Workflow failed."))

with tab_output:
    st.subheader("Latest workflow output")

    result = st.session_state.last_result
    if not result:
        st.info("Run a workflow from the **Run Workflow** tab to see output here.")
    elif result["status"] in {"denied", "error"}:
        _render_blocked_state(result)
        with st.expander("Raw JSON output"):
            st.json(result)
    else:
        st.success(f"Run ID: `{st.session_state.last_run_id}`")
        if result.get("agent_steps"):
            st.write("Orchestrated agent workflow completed.")
        elif result.get("skill_id"):
            st.write(f"Skill: `{result.get('skill_id')}`")
        _render_output(result)

with tab_analytics:
    st.subheader("Analytics & Reporting")
    st.caption("Phase 4 governed analytics workflow on synthetic structured data.")

    orch = st.session_state.last_orchestration
    if not orch or orch.get("workflow_type") != ANALYTICS_WORKFLOW:
        st.info(
            "Run the **Structured data analytics** workflow from the **Run Workflow** tab "
            "to see analytics and reporting results here."
        )
    elif orch.get("status") != "success":
        st.error(orch.get("reason") or orch.get("error", "Analytics workflow blocked or failed."))
        st.json(orch)
    else:
        st.success(f"Run ID: `{orch.get('run_id')}`")
        st.write(f"Data source: `{orch.get('data_source')}`")
        st.write(f"Workflow type: `{orch.get('workflow_type')}`")
        _render_output(orch)

with tab_memory:
    st.subheader("Memory & Recovery")
    st.caption("Phase 5 governed memory tiers, checkpoints, rollback, and dead-letter handling.")

    snapshot = ORCHESTRATOR.get_memory_snapshot()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Working memory preview**")
        if snapshot["working_memory"]:
            st.dataframe(snapshot["working_memory"], use_container_width=True)
        else:
            st.info("No working memory records yet.")
    with col2:
        st.markdown("**Session memory preview**")
        if snapshot["session_memory"]:
            st.dataframe(snapshot["session_memory"], use_container_width=True)
        else:
            st.info("No session memory records yet.")

    st.markdown("**Checkpoint list**")
    if snapshot["checkpoints"]:
        st.dataframe(snapshot["checkpoints"], use_container_width=True)
        latest = snapshot["checkpoints"][-1]
        st.write(f"Latest checkpoint status: `{latest.get('status')}`")
    else:
        st.info("No checkpoints yet. Run a workflow to create checkpoints.")

    st.markdown("**Quarantine memory**")
    if snapshot["quarantine"]:
        st.dataframe(snapshot["quarantine"], use_container_width=True)
    else:
        st.info("No quarantined outputs.")

    st.markdown("**Dead-letter queue**")
    if snapshot["dead_letter"]:
        st.dataframe(snapshot["dead_letter"], use_container_width=True)
    else:
        st.info("No dead-letter entries.")

    orch = st.session_state.last_orchestration
    if orch and orch.get("memory_actions"):
        st.markdown("**Latest run memory/recovery audit evidence**")
        st.dataframe(
            [
                {
                    "skill_id": action.get("skill_id"),
                    "status": action.get("status"),
                    "summary": (action.get("output") or {}).get("reason")
                    or (action.get("events") or [{}])[-1].get("summary", ""),
                }
                for action in orch.get("memory_actions", [])
                if isinstance(action, dict)
            ],
            use_container_width=True,
        )

    st.divider()
    st.markdown("### Phase 5 demos")
    demo_choice = st.selectbox(
        "Choose a memory/recovery demo",
        options=[
            "blocked invalid memory write",
            "quarantine unverified output",
            "checkpoint creation via workflow run",
            "resume from last checkpoint",
            "rollback to previous checkpoint",
            "dead-letter unresolved failure",
        ],
    )

    if st.button("Run memory/recovery demo"):
        owner = st.session_state.get("accountability_owner", "").strip() or "Demo Operator"
        charter_ok, _ = validate_charter(_charter_form_data())
        try:
            if demo_choice == "blocked invalid memory write":
                result = ORCHESTRATOR.demo_invalid_memory_write(
                    charter_complete=charter_ok,
                    accountability_owner=owner,
                )
            elif demo_choice == "quarantine unverified output":
                result = ORCHESTRATOR.demo_quarantine_unverified(
                    charter_complete=charter_ok,
                    accountability_owner=owner,
                )
            elif demo_choice == "checkpoint creation via workflow run":
                result = ORCHESTRATOR.run(
                    workflow_type="Structured data preview",
                    data_source="Synthetic structured database",
                    charter_complete=charter_ok,
                    accountability_owner=owner,
                )
                st.session_state.last_orchestration = result
                st.session_state.last_result = result
            elif demo_choice == "resume from last checkpoint":
                checkpoints = ORCHESTRATOR.checkpoint_manager.list_all(limit=5)
                if not checkpoints:
                    st.warning("No checkpoint available. Run a workflow first.")
                    result = {"status": "denied", "reason": "No checkpoint available."}
                else:
                    result = ORCHESTRATOR.resume_from_checkpoint(
                        checkpoint_id=str(checkpoints[-1]["checkpoint_id"]),
                        charter_complete=charter_ok,
                        accountability_owner=owner,
                    )
            elif demo_choice == "rollback to previous checkpoint":
                checkpoints = ORCHESTRATOR.checkpoint_manager.list_all(limit=5)
                if not checkpoints:
                    st.warning("No checkpoint available. Run a workflow first.")
                    result = {"status": "denied", "reason": "No checkpoint available."}
                else:
                    result = ORCHESTRATOR.rollback_to_checkpoint(
                        checkpoint_id=str(checkpoints[0]["checkpoint_id"]),
                        charter_complete=charter_ok,
                        accountability_owner=owner,
                    )
            else:
                result = ORCHESTRATOR.demo_dead_letter(
                    charter_complete=charter_ok,
                    accountability_owner=owner,
                )
        except Exception as exc:
            st.error(f"Unexpected error (should not happen): {exc}")
            result = {"status": "error", "error": str(exc)}

        st.session_state.last_memory_demo = result
        if result.get("status") == "success":
            if result.get("output", {}).get("quarantined"):
                st.warning(result["output"].get("reason", "Output quarantined."))
            else:
                st.success("Memory/recovery demo completed.")
        elif result.get("status") == "denied":
            st.warning(result.get("reason", "Demo blocked."))
        else:
            st.error(result.get("error") or result.get("reason", "Demo failed."))

        failure_class = (result.get("output") or {}).get("failure_class")
        if failure_class:
            st.write(
                f"Failure class: `{failure_class}` → "
                f"recommended action: `{recommended_action(failure_class)}`"
            )

        if result.get("output"):
            st.json(result["output"])

with tab_advanced:
    st.subheader("Advanced Governance & Evidence")
    st.caption("Phase 6 cost, trust, security, approval, incident, and evidence reporting.")

    gov_snapshot = ORCHESTRATOR.get_governance_snapshot()
    orch = st.session_state.last_orchestration

    col1, col2, col3 = st.columns(3)
    with col1:
        cost = (orch or {}).get("cost_summary") or {}
        st.metric("Cost status", cost.get("cost_status", "within_budget"))
        st.write("Run total:", cost.get("run_total_cost", 0))
    with col2:
        trust = (orch or {}).get("trust_summary") or {}
        st.metric("Trust level", trust.get("trust_level", "n/a"))
    with col3:
        security = (orch or {}).get("security_summary") or {}
        st.metric("Security status", "passed" if security.get("passed", True) else "failed")

    st.markdown("**Approval queue**")
    approvals = gov_snapshot.get("approvals") or (orch or {}).get("approval_records") or []
    if approvals:
        st.dataframe(approvals, use_container_width=True)
    else:
        st.info("No approval records yet.")

    st.markdown("**Incident reports**")
    incidents = gov_snapshot.get("incidents") or (orch or {}).get("incidents") or []
    if incidents:
        st.dataframe(incidents, use_container_width=True)
    else:
        st.info("No incident reports yet.")

    summary = (orch or {}).get("governance_summary")
    if summary:
        st.markdown("**Governance run summary**")
        st.write(f"Final verdict: `{summary.get('final_governance_verdict')}`")
        st.json(summary)
        export_paths = (orch or {}).get("evidence_export_paths") or summary.get("export_paths") or {}
        if export_paths:
            st.markdown("**Downloadable evidence artifacts**")
            for label, path in export_paths.items():
                file_path = Path(path)
                if file_path.exists():
                    st.download_button(
                        label=f"Download {label}",
                        data=file_path.read_bytes(),
                        file_name=file_path.name,
                        key=f"dl_{label}_{file_path.name}",
                    )

    st.divider()
    st.markdown("### Phase 6 demos")
    gov_demo = st.selectbox(
        "Choose an advanced governance demo",
        options=[
            "cost limit exceeded",
            "untrusted agent blocked",
            "security injection detected",
            "approval required for high-risk skill",
            "approval rejected",
            "approval overridden with justification",
            "incident report generated",
            "governance summary approved with limitations",
            "governance summary blocked",
        ],
    )
    if st.button("Run advanced governance demo"):
        owner = st.session_state.get("accountability_owner", "").strip() or "Demo Operator"
        charter_ok, _ = validate_charter(_charter_form_data())
        try:
            if gov_demo == "cost limit exceeded":
                result = ORCHESTRATOR.demo_cost_limit_exceeded(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "untrusted agent blocked":
                result = ORCHESTRATOR.demo_untrusted_agent_blocked(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "security injection detected":
                result = ORCHESTRATOR.demo_security_injection_detected(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "approval required for high-risk skill":
                result = ORCHESTRATOR.demo_approval_required(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "approval rejected":
                result = ORCHESTRATOR.demo_approval_rejected(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "approval overridden with justification":
                result = ORCHESTRATOR.demo_approval_override(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "incident report generated":
                result = ORCHESTRATOR.demo_incident_report(
                    charter_complete=charter_ok, accountability_owner=owner
                )
            elif gov_demo == "governance summary approved with limitations":
                result = ORCHESTRATOR.demo_governance_summary_with_limitations(
                    charter_complete=charter_ok, accountability_owner=owner
                )
                st.session_state.last_orchestration = result
            else:
                result = ORCHESTRATOR.demo_governance_summary_blocked(
                    charter_complete=charter_ok, accountability_owner=owner
                )
        except Exception as exc:
            st.error(str(exc))
            result = {"status": "error", "error": str(exc)}
        st.json(result)

with tab_agents:
    st.subheader("Agents & Orchestration")

    try:
        all_agents = get_all_agents()
        enabled_agents = get_enabled_agents()
    except Exception as exc:
        st.error(f"Unable to load agent registry: {exc}")
        all_agents = []
        enabled_agents = []

    st.markdown("### Registered agents")
    if all_agents:
        st.dataframe(all_agents, use_container_width=True)
        st.caption(f"{len(enabled_agents)} enabled / {len(all_agents)} registered")
    else:
        st.info("No agents loaded.")

    st.markdown("### Current orchestration sequence")
    st.code(
        "Preview/document:\n"
        + " → ".join(DEFAULT_AGENT_SEQUENCE)
        + "\n\nAnalytics:\n"
        + " → ".join(
            f"{agent}[{skill or 'default'}]" for agent, skill in ANALYTICS_STEP_SEQUENCE
        ),
        language="text",
    )

    st.divider()
    st.markdown("### Latest agent run result")
    orch = st.session_state.last_orchestration
    if orch:
        st.write(f"**Status:** `{orch.get('status')}`")
        st.write(f"**Run ID:** `{orch.get('run_id')}`")

        steps = orch.get("agent_steps", [])
        if steps:
            st.markdown("**Per-agent statuses**")
            status_rows = [
                {
                    "agent_id": step.get("agent_id"),
                    "agent_name": step.get("agent_name"),
                    "skill_id": step.get("skill_id"),
                    "execution_status": step.get("execution_status"),
                    "policy_decision": step.get("policy_decision"),
                    "pre_gate_status": step.get("pre_gate_status"),
                    "post_gate_status": step.get("post_gate_status"),
                    "output_summary": step.get("output_summary"),
                }
                for step in steps
            ]
            st.dataframe(status_rows, use_container_width=True)

            selected_step = st.selectbox(
                "Inspect agent step",
                options=list(range(len(steps))),
                format_func=lambda i: f"{steps[i].get('agent_name')} ({steps[i].get('skill_id')})",
            )
            step = steps[selected_step]
            if step.get("policy") or step.get("pre_gates"):
                st.markdown("**Policy / gate results for selected step**")
                if step.get("policy"):
                    st.json(step["policy"])
                if step.get("pre_gates"):
                    st.dataframe(step["pre_gates"], use_container_width=True)
                if step.get("post_gates"):
                    st.dataframe(step["post_gates"], use_container_width=True)
        if orch.get("final_summary"):
            st.markdown("**Final governed summary**")
            st.write(orch["final_summary"].get("summary_text", ""))
    else:
        st.info("Run a workflow from the **Run Workflow** tab to see orchestration results.")

    st.divider()
    st.markdown("### Agent failure demos")
    st.caption("Safe blocking scenarios for governed agents.")

    agent_demo = st.selectbox(
        "Choose an agent failure demo",
        options=[
            "incomplete charter blocks agent workflow",
            "missing accountability owner blocks agent workflow",
            "disabled agent blocks execution",
            "agent attempts unauthorized skill and is blocked",
            "invalid data source is blocked",
            "invalid workflow type is blocked",
        ],
    )

    if st.button("Run agent failure demo"):
        owner = st.session_state.get("accountability_owner", "").strip()
        form_data = _charter_form_data()
        charter_complete, _ = validate_charter(form_data)

        demo_kwargs: dict[str, Any] = {
            "workflow_type": "Structured data preview",
            "data_source": "Synthetic structured database",
            "charter_complete": charter_complete,
            "accountability_owner": owner or "Demo Operator",
        }

        if agent_demo == "incomplete charter blocks agent workflow":
            demo_kwargs["charter_complete"] = False
        elif agent_demo == "missing accountability owner blocks agent workflow":
            demo_kwargs["accountability_owner"] = ""
            demo_kwargs["charter_complete"] = True
        elif agent_demo == "disabled agent blocks execution":
            demo_kwargs["agent_sequence"] = [
                "intake_agent",
                "disabled_demo_agent",
                "analysis_agent",
                "verification_agent",
                "report_agent",
            ]
        elif agent_demo == "agent attempts unauthorized skill and is blocked":
            demo_kwargs["skill_overrides"] = {"analysis_agent": "report_writer"}
        elif agent_demo == "invalid data source is blocked":
            demo_kwargs["data_source"] = "Invalid data source"
        elif agent_demo == "invalid workflow type is blocked":
            demo_kwargs["workflow_type"] = "Invalid workflow"

        with st.spinner("Running agent failure demo..."):
            try:
                result = _run_orchestrated_workflow(**demo_kwargs)
            except Exception as exc:
                st.error(f"Unexpected error (should not happen): {exc}")
                result = {"status": "error", "error": str(exc)}

        st.session_state.last_orchestration = result
        st.session_state.last_result = result
        st.session_state.last_run_id = result.get("run_id")

        if result.get("status") == "denied":
            st.warning(result.get("reason", "Blocked as expected."))
        elif result.get("status") == "error":
            st.error(result.get("reason") or result.get("error", "Failed as expected."))
        else:
            st.info("Demo completed without blocking — check parameters.")

        if result.get("agent_steps"):
            st.dataframe(
                [
                    {
                        "agent_id": s.get("agent_id"),
                        "execution_status": s.get("execution_status"),
                        "output_summary": s.get("output_summary"),
                    }
                    for s in result["agent_steps"]
                ],
                use_container_width=True,
            )

with tab_governance:
    st.subheader("Skills Governance & Failure Demos")

    try:
        all_skills = get_all_skills()
        enabled_skills = get_enabled_skills()
    except Exception as exc:
        st.error(f"Unable to load skill registry: {exc}")
        all_skills = []
        enabled_skills = []

    st.markdown("### Registered skills")
    if all_skills:
        st.dataframe(all_skills, use_container_width=True)
        st.caption(f"{len(enabled_skills)} enabled / {len(all_skills)} registered")
    else:
        st.info("No skills loaded.")

    st.divider()
    st.markdown("### Latest execution governance")

    gov = st.session_state.last_governance
    if gov:
        st.write(f"**Selected skill:** `{gov.get('skill_id')}`")
        st.write(f"**Status:** `{gov.get('status')}`")

        if gov.get("policy"):
            st.markdown("**Policy decision**")
            st.json(gov["policy"])

        if gov.get("pre_gates"):
            st.markdown("**Pre-gate results**")
            st.dataframe(gov["pre_gates"], use_container_width=True)

        if gov.get("post_gates"):
            st.markdown("**Post-gate results**")
            st.dataframe(gov["post_gates"], use_container_width=True)

        if gov.get("output"):
            st.markdown("**Execution result**")
            st.json(gov["output"])
    else:
        st.info("Run a workflow or failure demo to see governance results here.")

    st.divider()
    st.markdown("### Intentional failure demos")
    st.caption("Safe denial scenarios — the app should not crash.")

    demo_choice = st.selectbox(
        "Choose a failure demo",
        options=[
            "unregistered skill",
            "disabled skill",
            "skill/data-source mismatch",
            "skill/workflow mismatch",
            "incomplete charter",
            "excessive input size",
            "approval-required skill blocked",
        ],
    )

    if st.button("Run failure demo"):
        owner = st.session_state.get("accountability_owner", "").strip() or "Demo Operator"
        form_data = _charter_form_data()
        charter_complete, _ = validate_charter(form_data)

        demo_params = {
            "skill_id": "structured_data_summary",
            "workflow_type": "Structured data preview",
            "data_source": "Synthetic structured database",
            "charter_complete": charter_complete,
            "accountability_owner": owner,
            "input_size": None,
        }

        if demo_choice == "unregistered skill":
            demo_params["skill_id"] = "nonexistent_skill"
        elif demo_choice == "disabled skill":
            demo_params["skill_id"] = "disabled_demo_skill"
        elif demo_choice == "skill/data-source mismatch":
            demo_params["data_source"] = "Synthetic document database"
        elif demo_choice == "skill/workflow mismatch":
            demo_params["workflow_type"] = "Document review preview"
        elif demo_choice == "incomplete charter":
            demo_params["charter_complete"] = False
        elif demo_choice == "excessive input size":
            demo_params["input_size"] = 9999
        elif demo_choice == "approval-required skill blocked":
            demo_params["skill_id"] = "approval_required_demo"

        with st.spinner("Running failure demo..."):
            try:
                result = _run_governed_skill(**demo_params)
            except Exception as exc:
                st.error(f"Unexpected error (should not happen): {exc}")
                result = {"status": "error", "error": str(exc)}

        st.session_state.last_governance = result
        st.session_state.last_result = result
        st.session_state.last_run_id = result.get("run_id")

        if result.get("status") == "denied":
            _render_blocked_state(result)
        elif result.get("status") == "error":
            _render_blocked_state(result)
        else:
            st.info("Demo completed without denial — check parameters.")

        if result.get("policy"):
            st.json(result["policy"])
        if result.get("pre_gates"):
            st.dataframe(result["pre_gates"], use_container_width=True)

    st.divider()
    st.markdown("### Recent skill audit entries")

    try:
        events = read_audit_events(limit=50)
    except RuntimeError as exc:
        st.error(str(exc))
        events = []

    skill_events = [event for event in events if event.get("skill_id")]
    if skill_events:
        st.dataframe(skill_events[-10:], use_container_width=True)
    else:
        st.info("No skill audit entries yet.")

with tab_audit:
    st.subheader("Audit / Evidence Viewer")

    refresh = st.button("Refresh audit log")
    if refresh:
        st.rerun()

    try:
        events = read_audit_events(limit=50)
    except RuntimeError as exc:
        st.error(str(exc))
        events = []

    if not events:
        st.info("No audit events yet. Run a workflow to create audit entries.")
    else:
        st.caption(f"Showing last {len(events)} event(s) from `storage/audit_log.jsonl`")
        st.dataframe(events, use_container_width=True)

        orch = st.session_state.last_orchestration
        if orch and orch.get("evidence_export_paths"):
            st.markdown("**Latest evidence artifacts**")
            for label, path in orch["evidence_export_paths"].items():
                file_path = Path(path)
                if file_path.exists():
                    st.download_button(
                        label=f"Download {label}",
                        data=file_path.read_bytes(),
                        file_name=file_path.name,
                        key=f"audit_tab_{label}",
                    )

        if st.session_state.last_run_id:
            run_events = [e for e in events if e.get("run_id") == st.session_state.last_run_id]
            if run_events:
                st.markdown("**Latest run events**")
                st.json(run_events)
