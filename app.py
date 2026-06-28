"""agentstack Phase 1 — governed intelligence stack foundation."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from governance.audit_logger import generate_run_id, read_audit_events
from governance.demo_workflow import run_demo_workflow
from governance.workflow_charter import (
    CHARTER_RULE,
    DATA_SOURCES,
    WORKFLOW_TYPES,
    charter_status_message,
    load_charter_text,
    validate_charter,
)

REPO_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "reports"

st.set_page_config(
    page_title="agentstack — Phase 1",
    page_icon="🛡️",
    layout="wide",
)

st.title("agentstack")
st.caption("Phase 1 — Governed multi-agent intelligence stack foundation")
st.info(f"**Governance rule:** {CHARTER_RULE}")

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_run_id" not in st.session_state:
    st.session_state.last_run_id = None


def _save_report(run_id: str, payload: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{run_id}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


tab_charter, tab_run, tab_output, tab_audit = st.tabs(
    ["Workflow Charter", "Run Workflow", "Output", "Audit Log"]
)

with tab_charter:
    st.subheader("Agent Charter")
    st.markdown(
        "Complete the checklist below before running a workflow. "
        f"**{CHARTER_RULE}**"
    )

    with st.expander("View full AGENT_CHARTER.md", expanded=False):
        try:
            st.markdown(load_charter_text())
        except RuntimeError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Run charter checklist")

    charter_form = {
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
        "workflow_scope_ack": st.checkbox(
            "Workflow scope confirmed (Phase 1 demo only)",
            key="workflow_scope_ack",
        ),
        "out_of_scope_ack": st.checkbox(
            "Out-of-scope activities excluded (no Phase 2+ features)",
            key="out_of_scope_ack",
        ),
        "audit_enabled_ack": st.checkbox(
            "Audit and observability enabled",
            key="audit_enabled_ack",
        ),
    }

    is_complete, missing = validate_charter(charter_form)
    message = charter_status_message(is_complete, missing)

    if is_complete:
        st.success(message)
    else:
        st.warning(message)

with tab_run:
    st.subheader("Run demonstration workflow")

    data_source = st.selectbox(
        "Data source",
        options=DATA_SOURCES,
        help="Phase 1 supports synthetic sources only.",
    )
    workflow_type = st.selectbox(
        "Workflow type",
        options=WORKFLOW_TYPES,
        help="Choose a workflow that matches your selected data source.",
    )

    st.caption("Workflow pairing guide")
    st.markdown(
        "- **Structured data preview** → Synthetic structured database\n"
        "- **Document review preview** → Synthetic document database"
    )

    if st.button("Run workflow", type="primary"):
        is_complete, missing = validate_charter(
            {
                "business_problem_ack": st.session_state.get("business_problem_ack", False),
                "desired_outcome_ack": st.session_state.get("desired_outcome_ack", False),
                "accountability_owner": st.session_state.get("accountability_owner", ""),
                "workflow_scope_ack": st.session_state.get("workflow_scope_ack", False),
                "out_of_scope_ack": st.session_state.get("out_of_scope_ack", False),
                "audit_enabled_ack": st.session_state.get("audit_enabled_ack", False),
            }
        )

        if not is_complete:
            st.error(charter_status_message(is_complete, missing))
            st.stop()

        run_id = generate_run_id()
        owner = st.session_state.get("accountability_owner", "").strip()

        with st.spinner("Running demo workflow..."):
            result = run_demo_workflow(
                run_id=run_id,
                workflow_type=workflow_type,
                data_source=data_source,
                accountability_owner=owner,
            )

        st.session_state.last_run_id = run_id
        st.session_state.last_result = result

        if result["status"] == "success":
            try:
                report_path = _save_report(run_id, result["output"])
                st.success(f"Workflow completed. Report saved to `{report_path.name}`.")
            except OSError as exc:
                st.warning(f"Workflow completed but report save failed: {exc}")
        else:
            st.error(result.get("error", "Workflow failed."))

with tab_output:
    st.subheader("Latest workflow output")

    result = st.session_state.last_result
    if not result:
        st.info("Run a workflow from the **Run Workflow** tab to see output here.")
    elif result["status"] == "error":
        st.error(result.get("error", "Unknown error"))
        st.json(result)
    else:
        st.success(f"Run ID: `{st.session_state.last_run_id}`")
        output = result["output"]
        summary = output.get("summary", {})

        if output["workflow_type"] == "Structured data preview":
            col1, col2, col3 = st.columns(3)
            col1.metric("Records", summary.get("record_count", 0))
            col2.metric("Total revenue (USD)", summary.get("total_revenue_usd", 0))
            col3.metric("Average revenue (USD)", summary.get("average_revenue_usd", 0))
            st.write("Regions:", ", ".join(summary.get("regions", [])))
            st.write("Categories:", ", ".join(summary.get("categories", [])))
            st.dataframe(output.get("records", []), use_container_width=True)
        elif output["workflow_type"] == "Document review preview":
            col1, col2 = st.columns(2)
            col1.metric("Documents", summary.get("document_count", 0))
            col2.metric("Risk tiers", len(summary.get("risk_counts", {})))
            st.write("Document types:", ", ".join(summary.get("doc_types", [])))
            st.write("Risk counts:", summary.get("risk_counts", {}))
            st.dataframe(output.get("documents", []), use_container_width=True)

        with st.expander("Raw JSON output"):
            st.json(output)

with tab_audit:
    st.subheader("Audit log")

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

        if st.session_state.last_run_id:
            run_events = [e for e in events if e.get("run_id") == st.session_state.last_run_id]
            if run_events:
                st.markdown("**Latest run events**")
                st.json(run_events)
