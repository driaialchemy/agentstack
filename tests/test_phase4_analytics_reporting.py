"""Phase 4 analytics and reporting tests for agentstack."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_registry import get_agent_by_id
from agents.report_agent import ReportAgent
from analytics.report_builder import build_analytics_report, verify_analytics_report
from governance.audit_logger import read_audit_events
from orchestration.linear_orchestrator import LinearAgentOrchestrator
from skills.skill_executor import ANALYTICS_WORKFLOW, execute_skill


def _sample_analytics_context() -> dict:
    return {
        "eda_result": {
            "row_count": 8,
            "interpretation": "EDA demo interpretation.",
        },
        "regression_result": {
            "target_variable": "revenue_usd",
            "feature_variables": ["period"],
            "r_squared": 0.91,
            "interpretation": "Regression demo interpretation.",
            "limitations": ["Synthetic demo data only."],
        },
        "forecast_result": {
            "forecast_horizon": 3,
            "projected_values": [{"period": 13, "projected_revenue_usd": 130000}],
            "interpretation": "Forecast demo interpretation.",
            "limitation_note": "Not guaranteed prediction.",
            "limitations": ["Not guaranteed prediction."],
        },
        "chart_result": {
            "chart_path": "storage/charts/demo.png",
            "chart_type": "line",
        },
    }


class Phase4AnalyticsReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "audit_log.jsonl"
        self.reports_dir = Path(self.tmp.name) / "reports"
        self.charts_dir = Path(self.tmp.name) / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator = LinearAgentOrchestrator(
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_eda_skill_returns_structured_output(self) -> None:
        result = execute_skill(
            run_id="eda-test",
            skill_id="run_eda",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "success")
        output = result["output"]
        self.assertIn("row_count", output)
        self.assertIn("columns", output)
        self.assertIn("numeric_summary", output)
        self.assertIn("missing_value_summary", output)
        self.assertIn("trend_summary", output)
        self.assertIn("interpretation", output)

    def test_regression_skill_returns_limitations(self) -> None:
        result = execute_skill(
            run_id="regression-test",
            skill_id="run_regression",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "success")
        output = result["output"]
        self.assertIn("target_variable", output)
        self.assertIn("feature_variables", output)
        self.assertIn("coefficients", output)
        self.assertIn("r_squared", output)
        self.assertIn("interpretation", output)
        self.assertTrue(output["limitations"])

    def test_fourier_forecast_skill_returns_limitation_note(self) -> None:
        result = execute_skill(
            run_id="forecast-test",
            skill_id="run_fourier_forecast",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "success")
        output = result["output"]
        self.assertIn("projected_values", output)
        self.assertIn("seasonal_components", output)
        self.assertIn("limitation_note", output)
        self.assertIn("not guaranteed", output["limitation_note"].lower())

    def test_chart_generation_creates_artifact(self) -> None:
        forecast = execute_skill(
            run_id="chart-forecast",
            skill_id="run_fourier_forecast",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        result = execute_skill(
            run_id="chart-test",
            skill_id="generate_chart",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            agent_context={
                "run_id": "chart-test",
                "forecast_result": forecast["output"],
            },
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "success")
        chart_path = Path(result["output"]["chart_path"])
        self.assertTrue(chart_path.exists())
        self.assertEqual(chart_path.suffix, ".png")

    def test_analytics_report_includes_required_sections(self) -> None:
        chart_file = self.charts_dir / "demo.png"
        chart_file.write_bytes(b"png")
        samples = _sample_analytics_context()
        samples["chart_result"]["chart_path"] = str(chart_file)
        report = build_analytics_report(
            run_id="report-test",
            accountability_owner="Tester",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            eda=samples["eda_result"],
            regression=samples["regression_result"],
            forecast=samples["forecast_result"],
            chart=samples["chart_result"],
            reports_dir=self.reports_dir,
        )
        self.assertIn("findings", report)
        self.assertIn("forecast", report)
        self.assertIn("governance_notes", report)
        self.assertIn("limitations", report)
        self.assertTrue(report["complete"])

    def test_report_verification_passes_for_complete_report(self) -> None:
        chart_file = self.charts_dir / "demo.png"
        chart_file.write_bytes(b"png")
        samples = _sample_analytics_context()
        samples["chart_result"]["chart_path"] = str(chart_file)
        report = build_analytics_report(
            run_id="verify-pass",
            accountability_owner="Tester",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            eda=samples["eda_result"],
            regression=samples["regression_result"],
            forecast=samples["forecast_result"],
            chart=samples["chart_result"],
            reports_dir=self.reports_dir,
        )
        verification = verify_analytics_report(report)
        self.assertTrue(verification["verified"])

    def test_report_verification_fails_for_incomplete_report(self) -> None:
        verification = verify_analytics_report({"complete": False, "limitations": []})
        self.assertFalse(verification["verified"])

        result = execute_skill(
            run_id="verify-fail",
            skill_id="verify_analytics_report",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            agent_context={"analytics_report": {"complete": False, "limitations": []}},
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        self.assertEqual(result["status"], "error")

    def test_unauthorized_agent_cannot_run_analytics_skill(self) -> None:
        agent_config = get_agent_by_id("report_agent")
        agent = ReportAgent(agent_config)  # type: ignore[arg-type]
        context = {
            "run_id": "unauthorized-analytics",
            "workflow_type": ANALYTICS_WORKFLOW,
            "data_source": "Synthetic structured database",
            "charter_complete": True,
            "accountability_owner": "Tester",
        }
        result = agent.run(
            context=context,
            skill_id_override="run_eda",
            reports_dir=self.reports_dir,
            log_path=self.log_path,
        )
        self.assertEqual(result["status"], "denied")

    def test_missing_charter_blocks_analytics_workflow(self) -> None:
        result = self.orchestrator.run(
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=False,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "denied")

    def test_missing_accountability_owner_blocks_analytics_workflow(self) -> None:
        result = self.orchestrator.run(
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="",
        )
        self.assertEqual(result["status"], "denied")

    def test_invalid_workflow_source_fails_safely(self) -> None:
        result = self.orchestrator.run(
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic document database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertIn(result["status"], {"denied", "error"})

    def test_orchestrator_runs_full_analytics_workflow(self) -> None:
        result = self.orchestrator.run(
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
        )
        self.assertEqual(result["status"], "success")
        self.assertTrue(result.get("analytics_verified"))
        self.assertIn("eda", result["analytics_results"])
        self.assertIn("regression", result["analytics_results"])
        self.assertIn("forecast", result["analytics_results"])
        self.assertIn("chart", result["analytics_results"])
        self.assertTrue(Path(result["report_path"]).exists())

    def test_audit_records_written_for_phase4_skill(self) -> None:
        execute_skill(
            run_id="audit-phase4",
            skill_id="run_eda",
            workflow_type=ANALYTICS_WORKFLOW,
            data_source="Synthetic structured database",
            charter_complete=True,
            accountability_owner="Tester",
            log_path=self.log_path,
            reports_dir=self.reports_dir,
        )
        events = read_audit_events(log_path=self.log_path)
        self.assertTrue(any(event.get("skill_id") == "run_eda" for event in events))


if __name__ == "__main__":
    unittest.main()
