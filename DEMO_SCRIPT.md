# agentstack — 7–10 Minute Demo Script

## Purpose

Show a **governed multi-agent intelligence stack** that runs synthetic workflows only, blocks unsafe actions, logs evidence, and produces audit-ready summaries.

**Portfolio proof statement:**

> I built a governed multi-agent intelligence stack that can review documents, analyze data, forecast trends, generate reports, and prove every agent action was controlled, logged, verified, and recoverable.

**Hard rule:** **No charter, no run.**

---

## 1. Launch (1 minute)

```powershell
cd C:\Users\msell\OneDrive\aialchemyrepos\agentstack
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the app in the browser. Point out the sidebar **Demo map** and the charter rule banner.

---

## 2. Complete the charter (1 minute)

Go to **Workflow Charter**.

- Check all checklist items.
- Enter an accountability owner (e.g. `Demo Operator`).
- Confirm the green success message.

Explain: nothing runs without a completed charter and named owner.

---

## 3. Run a governed workflow (2 minutes)

Go to **Run Workflow**.

- Data source: `Synthetic structured database`
- Workflow type: `Structured data preview`
- Click **Run workflow**

Then show **Output**:
- Structured summary metrics
- Run ID and governed result envelope (`success`, `status`, `message`)

Optional: rerun with **Structured data analytics** and open **Analytics & Reporting**.

---

## 4. Agents & orchestration (1 minute)

Open **Agents & Orchestration**.

- Show registered agents and allowed skills.
- Show the linear sequence: Intake → Analysis → Verification → Report.
- Expand the latest per-agent statuses, policy decision, and gate results.

Key point: agents do not call each other directly; they request governed skills.

---

## 5. Memory & recovery (1 minute)

Open **Memory & Recovery**.

- Working/session memory previews
- Checkpoint list after a successful run
- Mention quarantine and dead-letter as contamination controls

Optional: run one Phase 5 demo (e.g. blocked invalid memory write).

---

## 6. Advanced governance & evidence (1–2 minutes)

Open **Advanced Governance & Evidence**.

After a workflow run with evidence enabled, show:

- Cost status
- Trust level
- Security status
- Governance run summary and **final governance verdict**
- Download Markdown/JSON evidence artifacts

Explain: this is synthetic/demo governance, not production billing or certification.

---

## 7. One intentional failure demo (1 minute)

Go to **Skills Governance & Failure Demos**.

Run **incomplete charter** (uncheck a charter item first) or **unregistered skill**.

Show:

- Clear blocked message (not a crash)
- Failure class and recommended action
- Policy/gate details
- New audit entry in **Audit / Evidence Viewer**

---

## 8. Close (30 seconds)

Summarize the governed path:

```text
Streamlit UI → Charter validation → Orchestrator → Agent → Skill request
→ Policy engine → Gate engine → Skill executor → Audit logger
→ Memory/checkpoint/evidence → Verified output
```

Reiterate out of scope: no external APIs, no real client data, no autonomous loops, no production deployment.

---

## Pre-demo checklist

- [ ] `python -m pytest tests/ -v` passes
- [ ] Charter checklist can be completed
- [ ] Accountability owner filled in
- [ ] One successful workflow run completed before evidence tab demo
