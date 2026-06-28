# Agent Charter — agentstack

**Repository:** `agentstack`  
**Remote:** https://github.com/driaialchemy/agentstack  
**Charter version:** 1.0  
**Status:** Pre-implementation — defines the operating model before Phase 1 build begins  
**Effective rule:** **No charter, no run.**

---

## 1. Charter title

**AIAlchemy Governed Multi-Agent Intelligence Stack — Operating Charter**

This document is the mandatory workflow charter for the `agentstack` repository. No workflow, agent run, skill execution, or demo may proceed unless a completed charter instance exists, passes governance review, and is bound to that run.

---

## 2. Business problem

Organizations need intelligence workflows—document review, data analysis, forecasting, and reporting—that are useful *and* provably controlled. Most AI stacks are disconnected experiments: agents act without clear authority, outputs are not verified, failures are invisible, and audit evidence is missing.

`agentstack` addresses this by building **one integrated, governed multi-agent intelligence stack** (not ten separate apps) that can:

- Review documents and extract risks
- Analyze structured data and run projections (including Fourier-style seasonality modeling)
- Generate charts and reports
- Demonstrate governance around every agent, skill, decision, approval, failure, and output

The portfolio proof statement:

> “I built a governed multi-agent intelligence stack that can review documents, analyze data, forecast trends, generate reports, and prove every agent action was controlled, logged, verified, and recoverable.”

---

## 3. Desired outcome

Deliver a **Streamlit-based governed multi-agent intelligence stack** that:

| Capability | Requirement |
|---|---|
| Data | Uses built-in synthetic structured data and synthetic document corpus; optionally connects to `contractriskreviewpipeline` via adapter only |
| Workflows | Runs document review, advanced data analysis, projections/forecasting, and report generation |
| Governance | Shows charter, policy, gates, approvals, audit trail, verification, rollback, and evidence for every run |
| Demonstrability | Works safely without real client data or primary reliance on user uploads |
| Integration | Reuses patterns from prior AIAlchemy repos as modules, not as hard dependencies |

**Phase 1 outcome (first build target):** Streamlit shell, synthetic data sources, source selector, workflow charter tab, basic workflow runner, and basic audit log—nothing more until this charter is satisfied and Phase 1 gates pass.

---

## 4. Decision environment

| Dimension | Setting |
|---|---|
| **Deployment context** | Local/demo-first; synthetic data by default |
| **Data sensitivity** | No real client data in MVP; optional external pipeline via adapter only |
| **Autonomy level** | Agents execute only through orchestrator-routed, policy-governed skill calls |
| **Human role** | Approves plans, high-risk actions, overrides, and halts; inspects audit and evidence |
| **Build approach** | Phased (Phase 1 → 6); one phase at a time; no whole-stack single-prompt build |
| **Prior repos** | `AIAlchemy-Repo-Governor` (harness readiness), `ai-agent-governance` (control plane), `governance-logger` (audit), `Agent-Workflow-Review` (pre-run review), `workeragentcowork` (orchestration pattern), `contractriskreviewpipeline` (optional adapter source) |

**Architectural decision:** `agentstack` is the master repository. Prior repos contribute modules and patterns; they are not hardwired into the core stack.

---

## 5. Users and stakeholders

| Role | Responsibilities |
|---|---|
| **Executive / portfolio reviewer** | Evaluates governance story, evidence reports, and demo outcomes |
| **Human operator** | Selects data source and workflow, completes charter, approves plans and high-risk steps, halts runs, downloads reports |
| **Builder / coding agent** | Implements against this charter and phase plan; does not expand scope without charter amendment |
| **Governance arbiter (agent)** | Reviews workflow plans against charter, policy, and risk tier before execution proceeds |
| **Verifier (agent)** | Validates report and output quality before release |
| **Accountability owner** | Named human owner for each workflow run (see Section 23) |

---

## 6. Workflow scope

The stack supports these **in-scope workflow types**, selectable in the Streamlit UI:

| Workflow type | Primary skills (representative) |
|---|---|
| Contract / document review | `retrieve_document`, `review_document`, `extract_risks`, `generate_report`, `verify_report` |
| Risk analysis | Structured query, EDA, risk extraction, reporting, verification |
| Financial / data projection | `query_structured_data`, `run_eda`, `run_regression`, `run_fourier_forecast`, chart and report generation |
| Compliance review | Document/structured review with governance evidence outputs |
| Executive report | Summary, findings, charts, forecasts, recommendations, evidence, limitations |
| Governance audit report | Policy coverage, skill coverage, audit evidence, run summary |

**Data source options (all must normalize to internal records):**

- Synthetic structured database
- Synthetic document database
- Existing contract risk pipeline (via `contractriskreviewadapter` — optional, not hardwired)
- Hybrid: synthetic + existing

**MVP reference workflows:**

1. **Structured Data + Forecasting:** source → charter → plan → arbiter review → query → EDA → Fourier forecast → chart → report → verify → audit → download
2. **Synthetic Document Review:** source → charter → retrieve → review → extract risks → report → verify → audit → download

**Internal record types (data-source agnostic):** `DocumentRecord`, `StructuredDataRecord`, `RiskFinding`, `AnalysisResult`, `ForecastResult`, `ReportArtifact`, `AuditEvent`.

---

## 7. Out-of-scope activities

The following are **explicitly out of scope** unless this charter is amended and re-approved:

| Out of scope | Rationale |
|---|---|
| Building ten separate disconnected apps | Violates integrated-stack objective |
| Direct agent-to-agent messaging | All coordination via orchestrator |
| One monolithic agent doing all tasks | Use narrow, role-specific agents |
| Skipping audit logs or verification | Breaks governance proof story |
| Overbuilding compliance before demo works | Phase 6 handles advanced governance |
| Dependence on real client data | Demo must run on synthetic data |
| Primary reliance on user document uploads | Built-in synthetic corpus is default |
| Hardwiring to `contractriskreviewpipeline` | Adapter-only integration |
| Building the entire stack in one implementation pass | Phased build only |
| Phase 2–6 features during Phase 1 | Foundation first |
| Renaming the repository | Repository name is `agentstack` |
| Production deployment, SSO, or multi-tenant hosting | Future scope; not Phase 1 |

---

## 8. Agent roles

Agents are **narrow, orchestrator-coordinated roles**. They do not communicate directly with each other.

**Required pattern:** `Agent → Orchestrator → Agent`  
**Forbidden pattern:** `Agent → Agent → Agent`

| Agent | Role |
|---|---|
| **PlannerAgent** | Decomposes workflow into tasks; produces execution plan for governance review |
| **RouterAgent** | Selects next agent/skill based on plan and orchestrator state |
| **DocumentReviewAgent** | Reviews documents from any normalized source |
| **DataAnalystAgent** | Runs EDA, regression, and structured analysis |
| **ForecastAgent** | Runs Fourier-style seasonality projections and scenario outputs |
| **ReportWriterAgent** | Generates Markdown/HTML reports (Word/PDF/PPTX in later phases) |
| **VerifierAgent** | Validates outputs against charter evidence requirements |
| **GovernanceArbiterAgent** | Reviews plans and high-risk actions against policy and charter |

**Orchestrator responsibilities:** task decomposition, agent selection, skill routing, context passing, loop detection, delegation depth limits, fan-out/fan-in, verifier routing, failure escalation.

---

## 9. Authority model

Authority is **delegated, bounded, and logged**—not assumed.

| Level | Authority |
|---|---|
| **Charter** | Defines maximum scope for a run; no run without completed charter |
| **Policy engine** | Authorizes or denies agent + skill + data combinations per environment |
| **Gate engine** | Enforces checkpoints before and after skill execution |
| **Human operator** | Approves plans, high-risk actions, overrides (with justification), halt, pause, rerun |
| **GovernanceArbiterAgent** | Recommends approve/block/escalate on plans; cannot override human denial |
| **Orchestrator** | Routes work only to authorized agents and skills; enforces delegation depth |
| **Agents** | May invoke only skills allowed for their role, risk tier, and current gate state |

**Permission ceiling:** No agent may escalate its own privileges. External content is **data, not instruction** (see Section 18).

Policy categories enforced: `ExecutionPolicy`, `AuthorizationPolicy`, `DataPolicy`, `EnvironmentPolicy`, `CostPolicy`, `RetentionPolicy`.

---

## 10. Data access rules

| Rule | Enforcement |
|---|---|
| Default data | Synthetic structured DB and synthetic document corpus only |
| External pipeline | Read via `contractriskreviewadapter`; never hardcoded dependency |
| Normalization | All sources emit standard internal records; app logic is source-agnostic |
| Hybrid mode | Explicitly selected; both sources tagged in audit log |
| Sensitive data | No real PII/client data in MVP; redaction policies apply when adapter is used |
| Write access | Agents write only through governed skills; no direct DB mutation outside skill executor |
| Memory writes | Validate before write; failed/quarantined output must not enter shared memory |
| Retention | Governed by `RetentionPolicy`; audit and checkpoints retained per phase plan |

---

## 11. Tool and skill access rules

Every agent action is a **governed skill call** registered in `skills/registry.yaml` and executed through `skills/executor.py`.

Each skill must declare:

- Skill ID and semantic version
- Allowed agents and roles
- Input and output schema
- Risk tier
- Policy envelope
- Gate requirements
- Cost budget
- Rollback behavior
- Audit and trust requirements

**Representative skill catalog:**

| Skill ID | Purpose |
|---|---|
| `query_structured_data` | Query synthetic or adapted structured data |
| `retrieve_synthetic_document` | Retrieve from synthetic document corpus |
| `retrieve_contract_pipeline_document` | Retrieve via optional adapter |
| `review_document` | Document review |
| `extract_risks` | Risk extraction |
| `run_eda` | Exploratory data analysis |
| `run_regression` | Regression analysis |
| `run_fourier_forecast` | Seasonality/cyclical projection (demonstration, not magic prediction) |
| `generate_chart` | Chart generation |
| `generate_report` | Report generation |
| `verify_report` | Output verification |
| `log_audit_event` | Audit logging |

**Tool rules:**

- Tool allowlist only; no ad-hoc tool creation at runtime
- Skill definition hash verification before execution
- Untrusted agents blocked from high-trust skills
- Duplicate skill calls detected by `DuplicateDetectionGate`

---

## 12. Risk classification

| Tier | Description | Examples | Default handling |
|---|---|---|---|
| **Low** | Read synthetic data; generate non-binding summaries | EDA, chart preview | Auto-execute after charter validation |
| **Medium** | Analysis affecting report content | Regression, document review, risk extraction | Plan approval; post-execution output validation |
| **High** | Forecasts, external adapter reads, governance overrides | Fourier forecast, pipeline adapter, override with justification | Human approval gate required |
| **Critical** | Security violations, policy breaches, cost/quota exceedance | Injection detected, untrusted agent, quota failure | Halt, quarantine, escalate, alert |

**Intentional failure demos (Phase 2+):** bad input, quota failure, high-risk approval, duplicate call, cost limit, untrusted agent, rollback—governance must be visible when these fire.

Fourier-style projections are **demonstrations of seasonality/cyclical patterns**, not guaranteed predictions; reports must state limitations.

---

## 13. Human approval points

Human actions available in Streamlit: `approve`, `reject`, `pause`, `rerun`, `halt`, `override with justification`, `inspect state`, `download report`.

| Checkpoint | Trigger | Required action |
|---|---|---|
| **Charter completion** | Before any workflow run | Operator confirms charter fields complete |
| **Plan approval** | After PlannerAgent + GovernanceArbiter review | Operator approves or rejects execution plan |
| **High-risk skill gate** | Skill risk tier = High or Critical | Operator approval before skill runs |
| **Policy violation** | Policy engine blocks or flags action | Operator review in policy violation viewer |
| **Override** | Operator bypasses gate | Mandatory written justification logged to audit |
| **Emergency halt** | Operator or cascade failure | Immediate stop; no further skills until inspect/resume |
| **Report release** | Before download of unverified report | Block until VerifierAgent passes (or human accepts with justification) |

---

## 14. Evidence requirements

The system must prove governance happened. Required evidence artifacts:

| Artifact | Contents |
|---|---|
| **PolicyCoverageReport** | Which policies applied and passed/failed |
| **SkillCoverageReport** | Skills invoked, versions, agents, outcomes |
| **AuditEvidenceReport** | Full audit trail for the run |
| **IncidentReport** | Failure class, remediation, escalation path |
| **GovernanceRunSummary** | Charter ID, approvals, gates, costs, output hashes, accountability owner |

**Per-run minimum evidence fields:**

`run_id`, `task_id`, `agent_id`, `skill_id`, `skill_version`, `input_hash`, `output_hash`, `policy_decision`, `gate_result`, `approval_status`, `duration_ms`, `estimated_cost`, `failure_class`, `timestamp`, `parent_task_id`

Reports must include: executive summary, key findings, risks, charts, forecasts (where applicable), recommendations, **evidence references**, governance notes, and **limitations**.

---

## 15. Gate requirements

Gates are mandatory checkpoints managed by `governance/gate_engine.py`.

| Gate type | When applied |
|---|---|
| **PreExecutionGate** | Before every skill: schema valid, charter bound, agent authorized |
| **HumanApprovalGate** | High/critical risk or plan approval pending |
| **CostGate** | Estimated cost within budget |
| **QuotaGate** | Rate and volume limits not exceeded |
| **DuplicateDetectionGate** | Same skill+input not re-run without justification |
| **OutputValidationGate** | Skill output matches schema and quality checks |
| **SecurityGate** | Injection scan, permission ceiling, redaction rules |
| **DownstreamGate** | Downstream skill prerequisites satisfied |

**No gate pass, no skill run.** Failed gates must log failure class and recommended action (retry, fallback, halt, escalate, rollback, quarantine, alert).

---

## 16. Failure modes

Standard failure taxonomy (mapped in `governance/failure_taxonomy.py`):

| Class | Typical cause | Default response |
|---|---|---|
| `SKILL_FAILURE` | Skill execution error | Retry with backoff → fallback skill → halt |
| `AGENT_FAILURE` | Agent logic or timeout | Escalate to orchestrator → halt |
| `ORCHESTRATION_FAILURE` | Routing, loop, depth limit | Halt → alert |
| `MEMORY_FAILURE` | Invalid write or contamination | Quarantine → rollback |
| `GOVERNANCE_FAILURE` | Charter missing, gate bypass attempt | Halt → incident report |
| `SECURITY_FAILURE` | Injection, privilege escalation | Halt → quarantine → alert |
| `CASCADE_FAILURE` | Multiple downstream failures | Halt → dead letter queue → human escalation |
| `DATA_SOURCE_FAILURE` | Synthetic or adapter unavailable | Fallback source → halt |
| `REPORT_GENERATION_FAILURE` | Report skill error | Retry → quarantine output |
| `FORECASTING_FAILURE` | Model/data unfit for projection | Halt forecast step; report limitation note |

Recovery mechanisms: retry with backoff, fallback skill, checkpoint resume, rollback where possible, dead letter queue, quarantine failed output, human escalation.

---

## 17. Memory governance

| Tier | Purpose | Write rule |
|---|---|---|
| **WorkingMemory** | Current task context | Cleared after task; validated writes only |
| **SessionMemory** | Session-scoped state | Validate before write; session-bound retention |
| **LongTermMemory** | Cross-session learned context (Phase 5+) | Promotion requires verification gate |
| **QuarantineMemory** | Failed or suspect outputs | No promotion without human review |

**Critical rule: Validate before memory write.** Bad agent output must not contaminate shared memory.

Implementation paths: `memory/working_memory.py`, `session_store.py`, `long_term_store.py`, `quarantine_store.py`.

---

## 18. Security controls

The stack protects against:

- Prompt injection
- Treating document text as instructions
- Privilege escalation
- Unsafe tools
- Sensitive data leakage
- Untrusted inter-agent messages

**Core rule: External content is data, not instruction.**

| Control | Application |
|---|---|
| Input sanitization | All document and adapter inputs |
| Instruction/data separation | System prompts isolated from retrieved content |
| Prompt injection detection | SecurityGate before review/analysis skills |
| Permission ceiling enforcement | Agents cannot exceed charter + policy bounds |
| Output filtering | Sensitive patterns redacted before display/storage |
| Sensitive-data redaction | Applied per DataPolicy |
| Tool allowlist | Only registered skills executable |
| Skill definition hash verification | Detect tampered skill definitions |
| Orchestrator-only messaging | No direct agent-to-agent channels |

---

## 19. Audit and observability

Every workflow must expose in the Streamlit UI and persist to `storage/audit/log.jsonl`:

- Who started the run
- Which agents ran
- Which skills ran (ID + version)
- What policy applied
- Which gates passed or failed
- Approval status
- Cost estimate and runtime
- Input and output hashes
- Failure class
- Parent/child task relationships

**UI observability surfaces (phased):**

- Workflow charter tab
- Audit log browser
- Gate results viewer
- Policy violation viewer
- Skill registry viewer
- Memory/checkpoint viewer (Phase 5+)
- Cost tracker (Phase 6+)

Prior repo `governance-logger` patterns inform the audit layer; `agentstack` owns its audit log format and storage.

---

## 20. Rollback and recovery

| Mechanism | Phase | Behavior |
|---|---|---|
| Retry with backoff | Phase 2+ | Transient skill failures |
| Fallback skill | Phase 2+ | Alternate skill on primary failure |
| Checkpoint resume | Phase 5 | Resume workflow from last good checkpoint |
| Rollback | Phase 5 | Revert to prior checkpoint state where possible |
| Dead letter queue | Phase 5 | Failed tasks queued for human review |
| Quarantine | Phase 2+ | Suspect output isolated from memory and reports |
| Human escalation | All phases | Unrecoverable failures halt and notify operator |

Rollback demos must be included in Phase 2+ governance demos to make recovery visible.

---

## 21. Evaluation plan

| Phase | Evaluation focus | Success criteria |
|---|---|---|
| **Phase 1** | Foundation | Streamlit loads; synthetic sources selectable; charter tab blocks run without completion; basic audit log written |
| **Phase 2** | Skills governance | Skill registry loads; policy denies unauthorized calls; gate demos fail visibly; skill run logged |
| **Phase 3** | Agents/orchestration | MVP workflows execute via orchestrator; no direct agent calls; arbiter blocks bad plans |
| **Phase 4** | Analytics/reporting | EDA, regression, Fourier forecast produce charts; report verified before download |
| **Phase 5** | Memory/recovery | Checkpoint resume works; rollback demo succeeds; quarantine prevents contamination |
| **Phase 6** | Advanced governance | Evidence reports generated; cost/trust/security governance operational |

**Test coverage targets:** `tests/test_skills.py`, `test_policies.py`, `test_gates.py`, `test_orchestrator.py`, `test_forecasting.py`.

**Quality bar:** A run is successful only if charter was complete, gates passed, verification succeeded, and audit evidence is downloadable.

---

## 22. Monitoring plan

| Signal | Method | Action |
|---|---|---|
| Skill failure rate | Audit log aggregation | Alert on threshold; surface in governance dashboard |
| Gate failure rate | Gate result logs | Review policy tuning; run failure demos |
| Cost burn | Cost tracker (Phase 6) | CostGate blocks over-budget runs |
| Loop/delegation depth | Orchestrator metrics | Halt and log ORCHESTRATION_FAILURE |
| Verification failures | VerifierAgent outcomes | Block report download; quarantine output |
| Security events | SecurityGate logs | Halt run; IncidentReport |
| Run duration | `duration_ms` in audit | Flag anomalous long runs |

Phase 1 monitoring: basic audit log review and manual inspection in Streamlit. Automated aggregation added in later phases.

---

## 23. Accountability model

| Element | Requirement |
|---|---|
| **Accountability owner** | Named human operator recorded at charter binding time |
| **Run ownership** | Every `run_id` maps to one accountability owner |
| **Agent accountability** | Agents are accountable to orchestrator and policy engine, not to each other |
| **Override accountability** | Overrides require justification text, owner identity, and timestamp in audit log |
| **Evidence ownership** | Accountability owner receives GovernanceRunSummary at run completion |
| **Incident ownership** | Security and governance failures assign escalation to accountability owner |
| **Build accountability** | Coding agents implement only what this charter and active phase authorize |

---

## 24. Charter completion checklist

Before any workflow run, confirm all items:

- [ ] **Business problem** and **desired outcome** documented for this run
- [ ] **Decision environment** set (data source, workflow type, phase scope)
- [ ] **Users and stakeholders** identified; **accountability owner** named
- [ ] **Workflow scope** matches an in-scope workflow type (Section 6)
- [ ] **Out-of-scope activities** confirmed not included (Section 7)
- [ ] **Agent roles** assigned for this workflow path (Section 8)
- [ ] **Authority model** understood; no privilege escalation expected
- [ ] **Data access rules** satisfied for selected source (Section 10)
- [ ] **Tool/skill list** for this run identified and registered (Section 11)
- [ ] **Risk classification** assigned; high/critical steps flagged (Section 12)
- [ ] **Human approval points** identified (Section 13)
- [ ] **Evidence requirements** defined; output artifacts listed (Section 14)
- [ ] **Gate requirements** confirmed for each skill in plan (Section 15)
- [ ] **Failure modes** and responses acknowledged (Section 16)
- [ ] **Memory governance** rules apply if memory tier used (Section 17)
- [ ] **Security controls** active for document/external inputs (Section 18)
- [ ] **Audit and observability** enabled (Section 19)
- [ ] **Rollback and recovery** path known for this workflow (Section 20)
- [ ] **Evaluation plan** criteria for this phase understood (Section 21)
- [ ] **Monitoring plan** signals defined (Section 22)

**Hard stop:** If any checkbox is incomplete, the run must not start. Display: **“No charter, no run.”**

---

## 25. Ready-for-build assessment

### Repository identity

| Item | Status |
|---|---|
| Repository name | `agentstack` |
| Master repo role | Confirmed — prior repos are modules/adapters, not hard dependencies |
| Source charter | `chatgptcharter.md` (reference); **`AGENT_CHARTER.md` (enforceable)** |

### Phase 1 build authorization

Phase 1 may begin **only after** this charter is committed and reviewed. Phase 1 scope:

| In Phase 1 | Not in Phase 1 |
|---|---|
| Streamlit UI shell | Skill registry and policy engine (Phase 2) |
| Synthetic structured database | Full agent orchestration (Phase 3) |
| Synthetic document database | EDA, regression, Fourier forecast (Phase 4) |
| Data source dropdown | Memory tiers and checkpoints (Phase 5) |
| Workflow charter tab | Advanced cost/trust/security governance (Phase 6) |
| Basic workflow runner | Word/PDF/PPTX export |
| Basic audit log | Intentional failure demos |

### Readiness verdict

| Criterion | Met? |
|---|---|
| Enforceable charter document exists | **Yes** — this file |
| “No charter, no run” rule preserved | **Yes** — Section 24 |
| Scope bounded for Phase 1 | **Yes** — Sections 7 and 25 |
| Agent, skill, gate, and audit models defined | **Yes** — Sections 8–15, 19 |
| Security and failure handling defined | **Yes** — Sections 16, 18 |
| Accountability and evidence defined | **Yes** — Sections 14, 23 |
| Application code exists | **No** — intentional; build not started |
| Phase 1 implementation complete | **No** — next step after this charter |

### Decision

**The repository is ready for Phase 1 implementation.**

The coding agent may proceed to Phase 1 only: Streamlit app, synthetic data sources, source dropdown, workflow charter tab, basic workflow runner, and basic audit log. Do not scaffold agents, skills registry, policy gates, databases beyond synthetic seed data, or analytics until Phase 1 acceptance criteria pass.

---

*Charter derived from `chatgptcharter.md`. Placeholder name `ai-alchemy-agent-stack` superseded by `agentstack` throughout.*
