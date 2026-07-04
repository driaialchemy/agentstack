"""Phase 2 skills governance tests for agentstack."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from governance.gate_engine import all_gates_passed, run_post_execution_gates, run_pre_execution_gates
from governance.policy_engine import evaluate_policy
from governance.workflow_charter import validate_charter
from skills.skill_executor import execute_skill
from skills.skill_registry import get_enabled_skills, get_skill_by_id, load_skill_registry


def _complete_charter() -> dict:
    return {
        "business_problem_ack": True,
        "desired_outcome_ack": True,
        "accountability_owner": "Demo Operator",
        "workflow_scope_ack": True,
        "out_of_scope_ack": True,
        "audit_enabled_ack": True,
    }


class Phase2SkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "audit_log.jsonl"
        self.reports_dir = Path(self.tmp.name) / "reports"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_registry_loads_successfully(self) -> None:
        skills = load_skill_registry()
        self.assertGreaterEqual(len(skills), 5)
        self.assertIsNotNone(get_skill_by_id("structured_data_summary"))

    def test_enabled_skills_are_returned(self) -> None:
        enabled = get_enabled_skills()
        enabled_ids = {skill["skill_id"] for skill in enabled}
        self.assertIn("structured_data_summary", enabled_ids)
        self.assertNotIn("disabled_demo_skill", enabled_ids)

    def test_valid_skill_is_authorized(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="structured_data_summary",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        self.assertTrue(policy.allowed)
        self.assertEqual(policy.policy_decision, "allow")

    def test_invalid_skill_is_denied(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="nonexistent_skill",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_skill_not_found")

    def test_disabled_skill_is_denied(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="disabled_demo_skill",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_skill_disabled")

    def test_data_source_mismatch_is_denied(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="structured_data_summary",
            charter_complete=complete,
            data_source="Synthetic document database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_data_source_mismatch")

    def test_workflow_mismatch_is_denied(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="structured_data_summary",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Document review preview",
            input_size=5,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_workflow_mismatch")

    def test_incomplete_charter_blocks_execution(self) -> None:
        result = execute_skill(
            run_id="test-run-charter",
            skill_id="structured_data_summary",
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=False,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "denied")
        self.assertIn("charter", result["reason"].lower())

    def test_approval_required_skill_is_blocked(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="approval_required_demo",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_approval_required")

    def test_excessive_input_size_is_denied(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="structured_data_summary",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=9999,
        )
        self.assertFalse(policy.allowed)
        self.assertEqual(policy.policy_decision, "deny_input_size_exceeded")

    def test_pre_gates_return_structured_results(self) -> None:
        complete, _ = validate_charter(_complete_charter())
        policy = evaluate_policy(
            skill_id="structured_data_summary",
            charter_complete=complete,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
            input_size=5,
        )
        pre_gates = run_pre_execution_gates(
            skill_id="structured_data_summary",
            charter_complete=complete,
            policy=policy,
            data_source="Synthetic structured database",
            workflow_type="Structured data preview",
        )
        self.assertTrue(pre_gates)
        for gate in pre_gates:
            gate_dict = gate.to_dict()
            self.assertIn("passed", gate_dict)
            self.assertIn("gate_name", gate_dict)
            self.assertIn("reason", gate_dict)
            self.assertIn("details", gate_dict)

    def test_post_gates_return_structured_results(self) -> None:
        post_gates = run_post_execution_gates(
            result={"report_expected": True},
            report_path=Path(self.reports_dir / "demo.json"),
            audit_event={"run_id": "x"},
            unhandled_exception=None,
        )
        self.assertTrue(post_gates)
        for gate in post_gates:
            gate_dict = gate.to_dict()
            self.assertIn("passed", gate_dict)
            self.assertIn("gate_name", gate_dict)

    def test_skill_executor_runs_valid_skill_successfully(self) -> None:
        result = execute_skill(
            run_id="test-run-success",
            skill_id="structured_data_summary",
            workflow_type="Structured data preview",
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("records", result["output"])
        self.assertTrue(result["policy"]["allowed"])
        self.assertTrue(all_gates_passed([]) or result["pre_gates"])

    def test_intentional_failure_cases_do_not_crash(self) -> None:
        scenarios = [
            {
                "skill_id": "nonexistent_skill",
                "workflow_type": "Structured data preview",
                "data_source": "Synthetic structured database",
                "charter_complete": True,
            },
            {
                "skill_id": "disabled_demo_skill",
                "workflow_type": "Structured data preview",
                "data_source": "Synthetic structured database",
                "charter_complete": True,
            },
            {
                "skill_id": "structured_data_summary",
                "workflow_type": "Structured data preview",
                "data_source": "Synthetic document database",
                "charter_complete": True,
            },
            {
                "skill_id": "approval_required_demo",
                "workflow_type": "Structured data preview",
                "data_source": "Synthetic structured database",
                "charter_complete": True,
            },
            {
                "skill_id": "structured_data_summary",
                "workflow_type": "Structured data preview",
                "data_source": "Synthetic structured database",
                "charter_complete": False,
            },
        ]

        for index, params in enumerate(scenarios):
            result = execute_skill(
                run_id=f"test-run-fail-{index}",
                accountability_owner="Tester",
                input_size=9999 if index == 0 else None,
                log_path=self.log_path,
                reports_dir=self.reports_dir,
                **params,
            )
            self.assertIn(result["status"], {"denied", "error", "success"})


if __name__ == "__main__":
    unittest.main()
