"""Stabilization and hardening regression tests."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from governance.audit_logger import log_skill_event, read_audit_events
from orchestration.linear_orchestrator import LinearAgentOrchestrator
from skills.skill_executor import execute_skill


GOVERNED_RESULT_KEYS = {
    "success",
    "status",
    "message",
    "run_id",
    "workflow_type",
    "data_source",
    "accountability_owner",
    "errors",
    "warnings",
    "evidence_refs",
    "audit_refs",
}


class StabilizationHardeningTests(unittest.TestCase):
    def test_app_imports_safely(self) -> None:
        module = importlib.import_module("app")
        self.assertTrue(hasattr(module, "ORCHESTRATOR"))

    def test_blocked_state_result_shape_is_consistent(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        base = Path(tmp.name)
        orchestrator = LinearAgentOrchestrator(
            reports_dir=base / "reports",
            log_path=base / "audit.jsonl",
            checkpoint_dir=base / "checkpoints",
            working_memory_dir=base / "wm",
            session_memory_dir=base / "sm",
            quarantine_path=base / "q.jsonl",
            dead_letter_path=base / "dl.jsonl",
            approval_path=base / "approvals.jsonl",
            incident_dir=base / "incidents",
            evidence_dir=base / "evidence",
        )
        try:
            result = orchestrator.run(
                workflow_type="Structured data preview",
                data_source="Synthetic structured database",
                charter_complete=False,
                accountability_owner="Tester",
            )
        finally:
            tmp.cleanup()

        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["success"])
        self.assertTrue(GOVERNED_RESULT_KEYS.issubset(result.keys()))
        self.assertIn("failure_class", result)
        self.assertIn("recommended_action", result)

    def test_audit_events_contain_core_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit.jsonl"
            event = log_skill_event(
                run_id="audit-core-run",
                accountability_owner="Tester",
                skill_id="structured_data_summary",
                workflow_type="Structured data preview",
                data_source="Synthetic structured database",
                policy_decision="allow",
                pre_gate_status="passed",
                post_gate_status="passed",
                action="skill_executed",
                status="success",
                summary="Core field audit test.",
                log_path=log_path,
            )
            self.assertIn("gate_result", event)
            self.assertIn("skill_version", event)
            self.assertIn("task_id", event)
            events = read_audit_events(log_path=log_path)
            self.assertEqual(len(events), 1)

    def test_evidence_summary_generation_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            orchestrator = LinearAgentOrchestrator(
                reports_dir=base / "reports",
                log_path=base / "audit.jsonl",
                checkpoint_dir=base / "checkpoints",
                working_memory_dir=base / "wm",
                session_memory_dir=base / "sm",
                quarantine_path=base / "q.jsonl",
                dead_letter_path=base / "dl.jsonl",
                approval_path=base / "approvals.jsonl",
                incident_dir=base / "incidents",
                evidence_dir=base / "evidence",
            )
            result = orchestrator.demo_governance_summary_blocked(
                charter_complete=True,
                accountability_owner="Tester",
            )
        self.assertEqual(result["status"], "success")
        self.assertIn("final_governance_verdict", result["output"])

    def test_intentional_failure_demo_remains_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit.jsonl"
            result = execute_skill(
                run_id="stable-failure-run",
                skill_id="nonexistent_skill",
                workflow_type="Structured data preview",
                data_source="Synthetic structured database",
                charter_complete=True,
                accountability_owner="Tester",
                agent_context={"skip_approval_gate": True},
                log_path=log_path,
            )
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["success"])
        self.assertTrue(result.get("message"))

    def test_agents_do_not_directly_call_each_other(self) -> None:
        orchestrator_source = (
            REPO_ROOT / "orchestration" / "linear_orchestrator.py"
        ).read_text(encoding="utf-8")
        self.assertIn("agent.run(", orchestrator_source)
        self.assertNotIn("send_message", orchestrator_source)
        self.assertNotIn("delegate_to", orchestrator_source)

        agent_files = list((REPO_ROOT / "agents").glob("*_agent.py"))
        peer_names = [
            path.stem
            for path in agent_files
            if path.stem not in {"base_agent"}
        ]
        for path in agent_files:
            if path.stem == "base_agent":
                continue
            text = path.read_text(encoding="utf-8")
            for peer in peer_names:
                if peer == path.stem:
                    continue
                self.assertNotIn(
                    f"from agents.{peer}",
                    text,
                    msg=f"{path.name} must not import {peer}",
                )

    def test_analytics_does_not_bypass_skill_executor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit.jsonl"
            result = execute_skill(
                run_id="analytics-governed-run",
                skill_id="run_eda",
                workflow_type="Structured data analytics",
                data_source="Synthetic structured database",
                charter_complete=True,
                accountability_owner="Tester",
                agent_context={"skip_approval_gate": True},
                log_path=log_path,
            )
        self.assertEqual(result["status"], "success")
        self.assertIn("policy", result)
        self.assertIn("pre_gates", result)


if __name__ == "__main__":
    unittest.main()
