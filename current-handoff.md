# agentstack — current handoff

**Repo:** `C:\Users\msell\OneDrive\aialchemyrepos\agentstack`  
**Charter:** `AGENT_CHARTER.md` — **No charter, no run.**

## Completed status

- **Phases 1–6:** complete (governed stack through advanced governance/evidence)
- **Stabilization pass:** complete (result envelope, audit normalization, demo docs, regression tests)
- **Phase 7:** not started — do not add

## Latest test result

```text
81 passed in ~40s
python -m pytest tests/ -q
```

(Verified 2026-07-03)

## Recently created / modified (high signal only)

**Created (Phase 5–6 + stabilization):**

- `memory/`, `evidence/`, `governance/cost_tracker.py`, `trust_engine.py`, `security_engine.py`, `approval_queue.py`, `incident_report.py`, `result_contract.py`
- `agents/governance_agent.py`, `agents/recovery_agent.py`
- `tests/test_phase5_memory_recovery.py`, `test_phase6_advanced_governance.py`, `test_stabilization_hardening.py`
- `DEMO_SCRIPT.md`, `ARCHITECTURE.md`, `.cursor/plans/stabilization-hardening.md`

**Modified (integration + hardening):**

- `skills/skill_executor.py`, `skills/registry.yaml`
- `orchestration/linear_orchestrator.py`
- `governance/audit_logger.py`, `gate_engine.py`, `policy_engine.py`, `failure_taxonomy.py`
- `agents/registry.yaml`, `agents/base_agent.py`
- `app.py`, `README.md`

## Architecture summary

Linear governed path only — no agent-to-agent messaging, no autonomous loops, no dynamic routing:

```text
Streamlit UI → Charter validation → LinearAgentOrchestrator → Agent
→ execute_skill → Policy engine → Gate engine → Skill body
→ Audit logger → Memory/checkpoint/recovery → Evidence exports
```

Key dirs: `agents/`, `skills/`, `governance/`, `memory/`, `evidence/`, `orchestration/`, `analytics/`, `storage/`.

Docs: `ARCHITECTURE.md`, `DEMO_SCRIPT.md`, `README.md`.

## Known risks / unfinished work

- Full-suite run may occasionally flake on `test_orchestrator_runs_full_analytics_workflow` under load — re-run if it fails once.
- Evidence exports write to `storage/evidence/` when `enable_governance_evidence=True` (Run Workflow tab enables this).
- Cost/trust/security/approval gates activate only when context supplies evaluation data (by design).
- Live demo walkthrough via `DEMO_SCRIPT.md` not yet confirmed by a human dry-run in this session.

## Exact next task

**Demo-readiness validation (no new features):**

1. Run `streamlit run app.py`
2. Walk `DEMO_SCRIPT.md` end-to-end (charter → workflow → agents → memory → governance/evidence → one failure demo → audit viewer)
3. Fix only bugs found during that walkthrough — no Phase 7, no new capabilities

## Commands

```powershell
cd C:\Users\msell\OneDrive\aialchemyrepos\agentstack
python -m pytest tests/ -v
streamlit run app.py
```

## Strict out of scope

Do **not** add or expand:

- Phase 7 or new major capabilities
- External APIs, real client data, production deployment
- SSO, multi-tenant hosting, external compliance certification
- Autonomous loops, dynamic routing, agent-to-agent messaging
- Vector DBs, RAG, long-term memory tiers
- Full DLP, Word/PDF/PPTX export
- Contract risk pipeline hardwiring

Preserve existing Phase 1–6 behavior; all tests must stay green.
