# agentstack

**Governed multi-agent intelligence stack** — Phases 1–6 complete on synthetic data only.

See `AGENT_CHARTER.md` for the operating model. See `ARCHITECTURE.md` and `DEMO_SCRIPT.md` for structure and live demo steps.

**Governance rule:** No charter, no run.

## Project purpose

Demonstrate a single integrated stack where agents, skills, policy, gates, audit, memory/recovery, and evidence reporting work together. Every workflow must bind to a completed charter and accountability owner.

**Portfolio proof (combined phases):**

> I built a governed multi-agent intelligence stack that can produce evidence showing which agents acted, which skills were authorized, which gates passed or failed, what approvals were required, what risks were controlled, what failures occurred, and why the final output can or cannot be trusted.

## Current status

| Phase | Capability |
|-------|------------|
| 1 | Streamlit shell, charter, synthetic data, audit log |
| 2 | Skill registry, policy engine, gate engine, skill executor |
| 3 | Governed agents, linear orchestrator |
| 4 | Analytics & reporting on synthetic structured data |
| 5 | Memory, checkpoints, quarantine, recovery, dead-letter |
| 6 | Cost/trust/security governance, approvals, incidents, evidence exports |

Stabilization pass: consistent blocked-state envelopes, audit field normalization, demo UI clarity, regression tests in `tests/test_stabilization_hardening.py`.

## Install

```powershell
cd C:\Users\msell\OneDrive\aialchemyrepos\agentstack
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Launch Streamlit

```powershell
streamlit run app.py
```

Default URL: http://localhost:8501

## Run tests

```powershell
python -m pytest tests/ -v
```

## Key governance concepts

- **Charter gate:** incomplete charter blocks orchestration and governance skills.
- **Policy engine:** authorizes skills by registry, source, workflow, size, and approval state.
- **Gate engine:** pre/post checks; Phase 6 adds cost, trust, security, and human-approval gates when context supplies evaluations.
- **Skill executor:** sole execution path for skill and analytics logic.
- **Audit logger:** JSONL at `storage/audit_log.jsonl` with normalized fields where applicable.
- **Memory/recovery:** validate-before-write, checkpoints, quarantine, dead-letter.
- **Evidence:** policy/skill/audit summaries and governance verdict exported to `storage/evidence/`.

## Demo workflow (happy path)

1. Complete **Workflow Charter** (including accountability owner).
2. **Run Workflow** → `Structured data preview` + `Synthetic structured database`.
3. Review **Output**, **Agents & Orchestration**, **Memory & Recovery**.
4. Open **Advanced Governance & Evidence** for verdict and downloadable artifacts.
5. Inspect **Audit / Evidence Viewer** for run events.

For a guided walkthrough, use `DEMO_SCRIPT.md`.

## Intentional failure demos

| Tab | Examples |
|-----|----------|
| Skills Governance | unregistered skill, disabled skill, source/workflow mismatch, incomplete charter, excessive input, approval-required skill |
| Agents & Orchestration | incomplete charter, missing owner, disabled agent, unauthorized skill, invalid source/workflow |
| Memory & Recovery | invalid memory write, quarantine, checkpoint/resume/rollback, dead-letter |
| Advanced Governance | cost limit, untrusted agent, security injection, approval required/rejected/overridden, incident report, blocked summary |

Blocked paths return structured results with `failure_class` and `recommended_action` where appropriate.

## Repository structure

```text
agentstack/
  app.py
  AGENT_CHARTER.md
  ARCHITECTURE.md
  DEMO_SCRIPT.md
  agents/
  analytics/
  evidence/
  governance/
  memory/
  orchestration/
  skills/
  storage/
  reports/
  tests/
```

## Out of scope

External APIs, real client data, production deployment, SSO, multi-tenant hosting, autonomous loops, dynamic routing, vector databases, RAG memory, full DLP, external compliance certification, Word/PDF/PPTX export, contract risk pipeline hardwiring.

## License

See repository owner for license terms.
