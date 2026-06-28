# agentstack

**Governed multi-agent intelligence stack** — Phase 1 foundation for the `agentstack` repository.

Phase 1 delivers a working Streamlit shell with synthetic data sources, a workflow charter tab, a basic demonstration workflow runner, and a JSONL audit log. See `AGENT_CHARTER.md` for the full operating model.

**Governance rule:** No charter, no run.

## Phase 1 capabilities

- Streamlit app with four tabs: Workflow Charter, Run Workflow, Output, Audit Log
- Synthetic structured database (in-memory demo records)
- Synthetic document database (in-memory demo documents)
- Data source dropdown (synthetic sources only)
- Workflow charter checklist bound to `AGENT_CHARTER.md`
- Basic demo workflows:
  - Structured data preview
  - Document review preview
- JSONL audit log at `storage/audit_log.jsonl`
- Report artifacts saved to `reports/` as JSON

## Prerequisites

- Python 3.10 or newer
- pip

## Launch the app

From the repository root:

```bash
cd C:\Users\msell\OneDrive\aialchemyrepos\agentstack
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

The app opens in your browser (default: http://localhost:8501).

## Quick start

1. Open the **Workflow Charter** tab and complete the checklist (including accountability owner).
2. Open **Run Workflow**, select a data source and matching workflow type, then click **Run workflow**.
3. View results in **Output** and audit entries in **Audit Log**.

| Workflow type | Required data source |
|---|---|
| Structured data preview | Synthetic structured database |
| Document review preview | Synthetic document database |

## Run tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

Or run the smoke script directly:

```bash
python tests/test_phase1_smoke.py
```

## Project layout (Phase 1)

```text
agentstack/
  app.py
  AGENT_CHARTER.md
  requirements.txt
  data_sources/
    synthetic_data.py
    synthetic_documents.py
  governance/
    audit_logger.py
    workflow_charter.py
    demo_workflow.py
  storage/
    audit_log.jsonl
  reports/
  tests/
    test_phase1_smoke.py
```

## Out of scope (Phase 2+)

Phase 1 intentionally excludes skill registry, policy engine, gate engine, multi-agent orchestration, forecasting, memory tiers, rollback, approval queues, and `contractriskreviewpipeline` integration.

## License

See repository owner for license terms.
