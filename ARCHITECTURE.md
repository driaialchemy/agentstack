# agentstack Architecture

## System overview

`agentstack` is a Streamlit-based, linear multi-agent demo stack for synthetic data workflows. Every action passes through governed skills, policy, gates, and audit logging. Phases 1–6 are complete; there is no Phase 7 in this repository.

**Governance rule:** **No charter, no run.**

## Governed execution path

```text
Streamlit UI
→ Charter validation
→ Orchestrator
→ Agent
→ Governed skill request
→ Policy engine
→ Gate engine
→ Skill executor
→ Audit logger
→ Memory / checkpoint / evidence layer
→ Verified report / output
```

Agents do **not** message each other directly. The orchestrator passes shared context sequentially.

## Phase-by-phase architecture

| Phase | Focus |
|-------|--------|
| **1** | Streamlit shell, charter, synthetic data, basic workflow, JSONL audit |
| **2** | Skill registry, policy engine, gate engine, skill executor |
| **3** | Governed agents, linear orchestrator |
| **4** | Analytics modules (EDA, regression, forecast, charts, reports) via skills |
| **5** | Working/session/quarantine memory, checkpoints, recovery, dead-letter |
| **6** | Cost/trust/security governance, approvals, incidents, evidence exports |

## Folder structure

```text
agentstack/
  app.py                    # Streamlit demo UI
  AGENT_CHARTER.md          # Operating charter (source of truth)
  ARCHITECTURE.md           # This document
  DEMO_SCRIPT.md            # Live demo walkthrough
  agents/                   # Governed agent roles
  analytics/                # Synthetic analytics modules (Phase 4)
  evidence/                 # Policy/skill/audit/governance reports (Phase 6)
  governance/               # Policy, gates, audit, cost, trust, security, recovery
  memory/                   # Working, session, quarantine memory (Phase 5)
  orchestration/            # Linear orchestrator
  skills/                   # Registry + executor
  storage/                  # Audit log, checkpoints, approvals, evidence, etc.
  reports/                  # Generated report artifacts
  tests/                    # Phase and stabilization tests
```

## Agent model

- Each agent has a fixed `allowed_skills` list in `agents/registry.yaml`.
- Agents call `execute_skill()` only; they cannot bypass policy or gates.
- `BaseAgent` denies disabled agents and unauthorized skills before execution.

Registered agents include: Intake, Analysis, Verification, Report, Recovery, Governance.

## Skill governance model

- Skills are declared in `skills/registry.yaml` with data sources, workflow types, risk, cost metadata, and approval flags.
- `skills/skill_executor.py` is the only execution path for skill logic.
- Phase 6 governance skills (cost, trust, security, approval, evidence) use the same executor.

## Policy / gate model

**Policy engine** (`governance/policy_engine.py`):

- Charter complete
- Skill registered and enabled
- Data source / workflow match
- Input size limits
- Approval-required skills (unless pre-approved in context)

**Gate engine** (`governance/gate_engine.py`):

- Pre: charter, policy, skill exists/enabled, valid source/workflow
- Pre (Phase 6): CostGate, TrustGate, SecurityGate, HumanApprovalGate when context supplies evaluation data
- Post: result exists, report path (if expected), audit event, no unhandled exception

## Memory / recovery model

- **Working memory:** current step context (validated before write)
- **Session memory:** run state after success
- **Quarantine:** failed, suspect, or unverified outputs
- **Checkpoints:** created after successful major steps
- **Recovery manager:** quarantine, resume, rollback, dead-letter (deterministic, no autonomous loops)

## Evidence model

After a workflow (when `enable_governance_evidence=True`):

- Policy coverage report
- Skill coverage report
- Audit evidence report
- Governance run summary with final verdict: `approved`, `approved_with_limitations`, `blocked`, or `requires_human_review`

Exports land in `storage/evidence/` as Markdown and JSON.

## Result and audit consistency

Major blocked/success responses include a standard envelope via `governance/result_contract.py`:

- `success`, `status`, `message`, `run_id`, `workflow_type`, `data_source`, `accountability_owner`
- `data`, `errors`, `warnings`, `evidence_refs`, `audit_refs`
- `failure_class`, `recommended_action` when blocked

Audit events use `governance/audit_logger.py` with normalized fields where applicable (`gate_result`, `skill_version`, `failure_class`, etc.).

## Explicit out of scope

- External APIs and real client data
- Production deployment, SSO, multi-tenant hosting
- Autonomous loops and dynamic routing
- Vector databases and RAG memory
- Full DLP / external compliance certification
- Word/PDF/PPTX export (not required for demo)
- Contract risk pipeline hardwiring

## Key references

- Charter: `AGENT_CHARTER.md`
- Demo flow: `DEMO_SCRIPT.md`
- Tests: `python -m pytest tests/ -v`
