"""Phase 3 governed agents and orchestration tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_registry import get_agent_by_id, get_enabled_agents, load_agent_registry
from agents.analysis_agent import AnalysisAgent
from orchestration.linear_orchestrator import DEFAULT_AGENT_SEQUENCE, LinearAgentOrchestrator


def _complete_charter() -> dict:
    return {
        "business_problem_ack": True,
        "desired_outcome_ack": True,
        "accountability_owner": "Demo Operator",
        "workflow_scope_ack": True,
        "out_of_scope_ack": True,
        "audit_enabled_ack": True,
    }


class Phase3AgentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "audit_log.jsonl"
        self.reports_dir = Path(self.tmp.name) / "reports"
        self.orchestrator = LinearAgentOrchestrator(
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_agent_registry_loads_valid_agents(self) -> None:
        agents = load_agent_registry()
        self.assertGreaterEqual(len(agents), 4)
        self.assertIsNotNone(get_agent_by_id("intake_agent"))

    def test_disabled_agent_is_blocked(self) -> None:
        disabled = get_agent_by_id("disabled_demo_agent")
        self.assertIsNotNone(disabled)
        agent = AnalysisAgent(disabled)  # type: ignore[arg-type]
        context = {
            "run_id": "disabled-agent-test",
            "workflow_type": "Structured data preview",
            "data_source": "Synthetic structured database",
            "charter_complete": True,
            "accountability_owner": "Tester",
        }
        result = agent.run(
            context=context,
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("disabled", result["reason"].lower())

    def test_unknown_agent_is_blocked(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            agent_sequence=["unknown_agent"],
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("Unknown agent", result["reason"])

    def test_agent_cannot_use_unauthorized_skill(self) -> None:
        agent_config = get_agent_by_id("analysis_agent")
        agent = AnalysisAgent(agent_config)  # type: ignore[arg-type]
        context = {
            "run_id": "unauthorized-skill-test",
            "workflow_type": "Structured data preview",
            "data_source": "Synthetic structured database",
            "charter_complete": True,
            "accountability_owner": "Tester",
        }
        result = agent.run(
            context=context,
            skill_id_override="report_writer",
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "denied")
        self.assertEqual(result["policy_decision"], "deny_unauthorized_skill")

    def test_orchestrator_blocks_incomplete_charter(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=False,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("charter", result["reason"].lower())

    def test_orchestrator_blocks_missing_accountability_owner(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="",
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("Accountability owner", result["reason"])

    def test_orchestrator_runs_structured_workflow(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["agent_steps"]), 4)
        agent_ids = [step["agent_id"] for step in result["agent_steps"]]
        self.assertEqual(agent_ids, DEFAULT_AGENT_SEQUENCE)
        self.assertIn("records", result["analysis_output"])

    def test_orchestrator_runs_document_workflow(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Document review preview",
            data_source="Synthetic document database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("documents", result["analysis_output"])

    def test_orchestrator_stops_on_failed_policy_decision(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            skill_overrides={"analysis_agent": "report_writer"},
        )
        self.assertEqual(result["status"], "denied")
        self.assertEqual(len(result["agent_steps"]), 2)
        self.assertEqual(result["agent_steps"][0]["status"], "success")
        self.assertEqual(result["agent_steps"][1]["status"], "denied")

    def test_agent_audit_records_include_required_fields(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        step = result["agent_steps"][0]
        audit = step["audit_event"]
        required = {
            "run_id",
            "timestamp",
            "agent_id",
            "agent_name",
            "skill_id",
            "data_source",
            "workflow_type",
            "policy_decision",
            "pre_gate_status",
            "post_gate_status",
            "execution_status",
            "output_summary",
            "accountability_owner",
        }
        self.assertTrue(required.issubset(audit.keys()))

    def test_disabled_agent_in_sequence_blocks_execution(self) -> None:
        sequence = [
            "intake_agent",
            "disabled_demo_agent",
            "analysis_agent",
            "verification_agent",
            "report_agent",
        ]
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            agent_sequence=sequence,
        )
        self.assertEqual(result["status"], "denied")
        self.assertEqual(result["agent_steps"][1]["agent_id"], "disabled_demo_agent")

    def test_invalid_data_source_is_blocked(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Structured data preview",
            data_source="Invalid data source",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("Invalid data source", result["reason"])

    def test_invalid_workflow_type_is_blocked(self) -> None:
        result = self.orchestrator.run(
            workflow_type="Invalid workflow",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("Invalid workflow type", result["reason"])


if __name__ == "__main__":
    unittest.main()
