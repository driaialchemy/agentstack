"""Markdown/HTML analytics report builder for Phase 4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_analytics_report(
    *,
    run_id: str,
    accountability_owner: str,
    workflow_type: str,
    data_source: str,
    eda: dict[str, Any],
    regression: dict[str, Any],
    forecast: dict[str, Any],
    chart: dict[str, Any],
    reports_dir: Path,
) -> dict[str, Any]:
    """Build JSON, Markdown, and HTML report artifacts."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    findings = {
        "eda_interpretation": eda.get("interpretation"),
        "regression_interpretation": regression.get("interpretation"),
        "forecast_interpretation": forecast.get("interpretation"),
    }
    limitations = list(
        dict.fromkeys(
            (regression.get("limitations") or [])
            + (forecast.get("limitations") or [])
            + [
                "Synthetic structured data only.",
                "Governed demo workflow; not client-ready analysis.",
            ]
        )
    )
    governance_notes = [
        "Workflow executed through governed skills, policy engine, and gate engine.",
        f"Accountability owner: {accountability_owner}.",
        "All agent steps logged to audit_log.jsonl.",
    ]

    report_payload = {
        "report_id": run_id,
        "workflow_type": workflow_type,
        "data_source": data_source,
        "accountability_owner": accountability_owner,
        "findings": findings,
        "eda": eda,
        "regression": regression,
        "forecast": forecast,
        "chart": chart,
        "governance_notes": governance_notes,
        "limitations": limitations,
        "complete": True,
        "synthetic_data_notice": True,
    }

    json_path = reports_dir / f"{run_id}_analytics.json"
    md_path = reports_dir / f"{run_id}_analytics.md"
    html_path = reports_dir / f"{run_id}_analytics.html"

    json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    markdown = _render_markdown(report_payload)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(_render_html(report_payload, markdown), encoding="utf-8")

    report_payload["json_path"] = str(json_path)
    report_payload["markdown_path"] = str(md_path)
    report_payload["html_path"] = str(html_path)
    report_payload["formats"] = ["json", "markdown", "html"]
    return report_payload


def verify_analytics_report(report: dict[str, Any] | None) -> dict[str, Any]:
    """Verify a generated analytics report without modifying it."""
    required_sections = [
        "findings",
        "eda",
        "regression",
        "forecast",
        "chart",
        "governance_notes",
        "limitations",
    ]
    if not report:
        return {
            "verified": False,
            "message": "Analytics report is missing.",
            "missing_sections": required_sections,
        }

    missing = [section for section in required_sections if section not in report]
    if missing:
        return {
            "verified": False,
            "message": f"Analytics report missing sections: {', '.join(missing)}",
            "missing_sections": missing,
        }

    if not report.get("complete"):
        return {
            "verified": False,
            "message": "Analytics report is marked incomplete.",
            "missing_sections": [],
        }

    if not report.get("limitations"):
        return {
            "verified": False,
            "message": "Analytics report must include limitations.",
            "missing_sections": ["limitations"],
        }

    for path_key in ("json_path", "markdown_path", "html_path"):
        path_value = report.get(path_key)
        if not path_value or not Path(path_value).exists():
            return {
                "verified": False,
                "message": f"Report artifact missing: {path_key}",
                "missing_sections": [],
            }

    return {
        "verified": True,
        "message": "Analytics report verified successfully.",
        "checks_passed": required_sections + ["artifact_paths", "limitations_present"],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Governed Analytics Report (Synthetic Demo)",
        "",
        f"**Workflow:** {report['workflow_type']}",
        f"**Data source:** {report['data_source']}",
        f"**Accountability owner:** {report['accountability_owner']}",
        "",
        "## Findings",
        f"- EDA: {report['findings']['eda_interpretation']}",
        f"- Regression: {report['findings']['regression_interpretation']}",
        f"- Forecast: {report['findings']['forecast_interpretation']}",
        "",
        "## Governance notes",
    ]
    lines.extend(f"- {note}" for note in report["governance_notes"])
    lines.append("")
    lines.append("## Limitations")
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    lines.append(
        "_This report was generated from synthetic structured data as a governed demonstration._"
    )
    return "\n".join(lines)


def _render_html(report: dict[str, Any], markdown_body: str) -> str:
    escaped = (
        markdown_body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>\n")
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Governed Analytics Report</title></head><body>"
        f"<pre>{escaped}</pre></body></html>"
    )
