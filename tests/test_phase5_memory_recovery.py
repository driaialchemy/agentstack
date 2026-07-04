"""Phase 5 memory and recovery tests for agentstack."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_registry import get_agent_by_id
from agents.report_agent import ReportAgent
from governance.checkpoint_manager import CheckpointManager
from governance.dead_letter_queue import DeadLetterQueue
from memory.memory_validator import validate_memory_write
from memory.quarantine_store import QuarantineStore
from memory.working_memory import WorkingMemory
from orchestration.linear_orchestrator import LinearAgentOrchestrator
from skills.skill_executor import execute_skill


class Phase5MemoryRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.log_path = base / "audit_log.jsonl"
        self.reports_dir = base / "reports"
        self.checkpoint_dir = base / "checkpoints"
        self.working_dir = base / "memory" / "working"
        self.session_dir = base / "memory" / "session"
        self.quarantine_path = base / "quarantine" / "quarantine.jsonl"
        self.dead_letter_path = base / "dead_letter" / "dead_letter.jsonl"
        self.orchestrator = LinearAgentOrchestrator(
            reports_dir=self.reports_dir,
            log_path=self.log_path,
            checkpoint_dir=self.checkpoint_dir,
            working_memory_dir=self.working_dir,
            session_memory_dir=self.session_dir,
            quarantine_path=self.quarantine_path,
            dead_letter_path=self.dead_letter_path,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _base_context(self, run_id: str = "memory-test-run") -> dict:
        return {
            "run_id": run_id,
            "charter_complete": True,
            "accountability_owner": "Tester",
            "workflow_type": "Structured data preview",
            "data_source": "Synthetic structured database",
            "checkpoint_dir": str(self.checkpoint_dir),
            "working_memory_dir": str(self.working_dir),
            "session_memory_dir": str(self.session_dir),
            "quarantine_path": str(self.quarantine_path),
            "dead_letter_path": str(self.dead_letter_path),
        }

    def test_valid_working_memory_write_succeeds(self) -> None:
        context = self._base_context()
        context["memory_payload"] = {
            "run_id": context["run_id"],
            "accountability_owner": "Tester",
            "workflow_type": context["workflow_type"],
            "data_source": context["data_source"],
            "structured": True,
            "status": "success",
            "step": "intake_complete",
        }
        result = execute_skill(
            run_id=context["run_id"],
            skill_id="write_working_memory",
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            charter_complete=True,
            accountability_owner="Tester",
            agent_context=context,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["output"]["written"])
        stored = WorkingMemory(self.working_dir).read(context["run_id"])
        self.assertIsNotNone(stored)

    def test_invalid_memory_write_is_blocked(self) -> None:
        result = self.orchestrator.demo_invalid_memory_write(
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["output"]["quarantined"])

    def test_unverified_output_routes_to_quarantine(self) -> None:
        result = self.orchestrator.demo_quarantine_unverified(
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertTrue(result["output"]["quarantined"])
        entries = QuarantineStore(self.quarantine_path).list_entries()
        self.assertGreaterEqual(len(entries), 1)

    def test_failed_output_routes_to_quarantine(self) -> None:
        context = self._base_context("failed-output-run")
        context["memory_payload"] = {
            "run_id": context["run_id"],
            "accountability_owner": "Tester",
            "workflow_type": context["workflow_type"],
            "data_source": context["data_source"],
            "structured": True,
            "status": "failed",
        }
        valid, _, _ = validate_memory_write(context["memory_payload"], context)
        self.assertFalse(valid)

    def test_checkpoint_created_after_successful_step(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(len(result["checkpoints"]), 1)

    def test_checkpoint_contains_required_fields(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        checkpoint = result["checkpoints"][0]
        for field in (
            "checkpoint_id",
            "run_id",
            "accountability_owner",
            "current_step",
            "status",
            "output_refs",
        ):
            self.assertIn(field, checkpoint)

    def test_resume_from_checkpoint_returns_structured_state(self) -> None:
        run = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        checkpoint_id = run["last_checkpoint_id"]
        resumed = self.orchestrator.resume_from_checkpoint(
            checkpoint_id=str(checkpoint_id),
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(resumed["status"], "success")
        self.assertEqual(resumed["output"]["status"], "resumed")
        self.assertIn("agent_context", resumed["output"])

    def test_rollback_returns_prior_checkpoint_state(self) -> None:
        run = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        checkpoint_id = run["checkpoints"][0]["checkpoint_id"]
        rolled = self.orchestrator.rollback_to_checkpoint(
            checkpoint_id=str(checkpoint_id),
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(rolled["status"], "success")
        self.assertEqual(rolled["output"]["status"], "rolled_back")

    def test_dead_letter_records_unresolved_failure(self) -> None:
        result = self.orchestrator.demo_dead_letter(
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        entries = DeadLetterQueue(self.dead_letter_path).list_entries()
        self.assertGreaterEqual(len(entries), 1)
        self.assertIn("failure_class", entries[-1])

    def test_unauthorized_agent_cannot_write_memory(self) -> None:
        agent_config = get_agent_by_id("report_agent")
        agent = ReportAgent(agent_config)  # type: ignore[arg-type]
        context = self._base_context("unauthorized-memory")
        result = agent.run(
            context=context,
            skill_id_override="write_working_memory",
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "denied")

    def test_missing_charter_blocks_memory_write(self) -> None:
        context = self._base_context("charter-block")
        context["memory_payload"] = {
            "run_id": context["run_id"],
            "accountability_owner": "Tester",
            "workflow_type": context["workflow_type"],
            "data_source": context["data_source"],
            "structured": True,
            "status": "success",
        }
        result = execute_skill(
            run_id=context["run_id"],
            skill_id="write_working_memory",
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            charter_complete=False,
            accountability_owner="Tester",
            agent_context=context,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "denied")

    def test_missing_accountability_owner_blocks_checkpoint_creation(self) -> None:
        context = self._base_context("owner-block")
        context["checkpoint_step"] = "intake_complete"
        context["completed_steps"] = ["intake_complete"]
        result = execute_skill(
            run_id=context["run_id"],
            skill_id="create_checkpoint",
            workflow_type=context["workflow_type"],
            data_source=context["data_source"],
            charter_complete=True,
            accountability_owner="",
            agent_context=context,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
