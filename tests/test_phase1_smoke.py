"""Phase 1 smoke tests for agentstack."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from data_sources.synthetic_data import get_structured_records, summarize_structured_data
from data_sources.synthetic_documents import get_documents, summarize_documents
from governance.audit_logger import generate_run_id, log_event, read_audit_events
from governance.demo_workflow import run_demo_workflow
from governance.workflow_charter import (
    CHARTER_RULE,
    REQUIRED_CHARTER_FIELDS,
    load_charter_text,
    validate_charter,
)


class Phase1SmokeTests(unittest.TestCase):
    def test_charter_file_loads(self) -> None:
        text = load_charter_text()
        self.assertIn("agentstack", text)
        self.assertIn(CHARTER_RULE, text)

    def test_charter_validation_blocks_incomplete_runs(self) -> None:
        complete, missing = validate_charter(
            {
                "business_problem_ack": True,
                "desired_outcome_ack": True,
                "accountability_owner": "Demo Operator",
                "workflow_scope_ack": True,
                "out_of_scope_ack": True,
                "audit_enabled_ack": True,
            }
        )
        self.assertTrue(complete)
        self.assertEqual(missing, [])

        incomplete, missing = validate_charter({"accountability_owner": ""})
        self.assertFalse(incomplete)
        self.assertTrue(missing)

    def test_charter_required_field_names_are_stable(self) -> None:
        self.assertEqual(
            [field_name for field_name, _ in REQUIRED_CHARTER_FIELDS],
            [
                "business_problem_ack",
                "desired_outcome_ack",
                "accountability_owner",
                "workflow_scope_ack",
                "out_of_scope_ack",
                "audit_enabled_ack",
            ],
        )

    def test_accountability_owner_requires_non_empty_value(self) -> None:
        complete, missing = validate_charter(
            {
                "business_problem_ack": True,
                "desired_outcome_ack": True,
                "accountability_owner": "   ",
                "workflow_scope_ack": True,
                "out_of_scope_ack": True,
                "audit_enabled_ack": True,
            }
        )
        self.assertFalse(complete)
        self.assertIn("Accountability owner named", missing)

    def test_charter_validation_passes_when_all_acknowledgments_present(self) -> None:
        complete, missing = validate_charter(
            {
                "business_problem_ack": True,
                "desired_outcome_ack": True,
                "accountability_owner": "Demo Operator",
                "workflow_scope_ack": True,
                "out_of_scope_ack": True,
                "audit_enabled_ack": True,
            }
        )
        self.assertTrue(complete)
        self.assertEqual(missing, [])

    def test_charter_validation_reports_specific_missing_acknowledgments(self) -> None:
        """Regression test: desired outcome, out-of-scope, and audit acks must be
        read using validator field names (desired_outcome_ack, out_of_scope_ack,
        audit_enabled_ack), or the UI will misreport them as missing."""
        complete, missing = validate_charter(
            {
                "business_problem_ack": True,
                "desired_outcome_ack": False,
                "accountability_owner": "Demo Operator",
                "workflow_scope_ack": True,
                "out_of_scope_ack": False,
                "audit_enabled_ack": False,
            }
        )
        self.assertFalse(complete)
        self.assertEqual(
            missing,
            [
                "Desired outcome acknowledged",
                "Out-of-scope activities excluded",
                "Audit and observability enabled",
            ],
        )

    def test_synthetic_data_sources(self) -> None:
        records = get_structured_records()
        self.assertGreaterEqual(len(records), 3)
        summary = summarize_structured_data()
        self.assertEqual(summary["record_count"], len(records))

        documents = get_documents()
        self.assertGreaterEqual(len(documents), 3)
        doc_summary = summarize_documents()
        self.assertEqual(doc_summary["document_count"], len(documents))

    def test_audit_logger_writes_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit_log.jsonl"
            run_id = generate_run_id()
            event = log_event(
                run_id=run_id,
                workflow_type="Structured data preview",
                data_source="Synthetic structured database",
                action="test_action",
                status="success",
                summary="Smoke test event",
                log_path=log_path,
            )
            required = {
                "run_id",
                "timestamp",
                "workflow_type",
                "data_source",
                "action",
                "status",
                "summary",
            }
            self.assertTrue(required.issubset(event.keys()))

            events = read_audit_events(log_path=log_path)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["run_id"], run_id)

    def test_demo_workflow_structured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit_log.jsonl"
            run_id = generate_run_id()

            # Patch log path by monkeypatching through direct log calls in workflow
            # Run workflow uses default path; test via isolated log first then workflow
            result = run_demo_workflow(
                run_id=run_id,
                workflow_type="Structured data preview",
                data_source="Synthetic structured database",
                accountability_owner="Tester",
            )
            self.assertEqual(result["status"], "success")
            self.assertIn("records", result["output"])
            self.assertGreaterEqual(len(result["events"]), 2)

    def test_demo_workflow_document(self) -> None:
        run_id = generate_run_id()
        result = run_demo_workflow(
            run_id=run_id,
            workflow_type="Document review preview",
            data_source="Synthetic document database",
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("documents", result["output"])

    def test_demo_workflow_mismatch_fails(self) -> None:
        run_id = generate_run_id()
        result = run_demo_workflow(
            run_id=run_id,
            workflow_type="Structured data preview",
            data_source="Synthetic document database",
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("requires", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
