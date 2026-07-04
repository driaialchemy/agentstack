"""Incident reporting for Phase 6 governance failures."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from governance.failure_taxonomy import incident_severity, recommended_action

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INCIDENT_DIR = REPO_ROOT / "storage" / "incidents"


class IncidentReporter:
    """Create and store structured incident reports."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_INCIDENT_DIR

    def create(
        self,
        *,
        run_id: str,
        failure_class: str,
        triggering_agent: str,
        triggering_skill: str,
        policy_decision: str,
        gate_result: dict[str, Any] | None,
        security_result: dict[str, Any] | None,
        recovery_action: str,
        accountability_owner: str,
        recommended_next_action: str | None = None,
    ) -> dict[str, Any]:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        incident_id = str(uuid4())
        report = {
            "incident_id": incident_id,
            "run_id": run_id,
            "failure_class": failure_class,
            "severity": incident_severity(failure_class),
            "triggering_agent": triggering_agent,
            "triggering_skill": triggering_skill,
            "policy_decision": policy_decision,
            "gate_result": gate_result or {},
            "security_result": security_result or {},
            "recovery_action": recovery_action,
            "accountability_owner": accountability_owner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommended_next_action": recommended_next_action
            or recommended_action(failure_class),
        }
        path = self.base_dir / f"{incident_id}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def list_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.base_dir.exists():
            return []
        reports: list[dict[str, Any]] = []
        for path in sorted(self.base_dir.glob("*.json")):
            try:
                reports.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        if limit is not None:
            return reports[-limit:]
        return reports
