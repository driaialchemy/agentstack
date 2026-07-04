"""Failure taxonomy and recommended actions for Phase 5–6."""

from __future__ import annotations

FAILURE_CLASSES = [
    "SKILL_FAILURE",
    "AGENT_FAILURE",
    "ORCHESTRATION_FAILURE",
    "MEMORY_FAILURE",
    "GOVERNANCE_FAILURE",
    "SECURITY_FAILURE",
    "CASCADE_FAILURE",
    "DATA_SOURCE_FAILURE",
    "REPORT_GENERATION_FAILURE",
    "FORECASTING_FAILURE",
    "CHECKPOINT_FAILURE",
    "ROLLBACK_FAILURE",
    "QUARANTINE_FAILURE",
    "COST_FAILURE",
    "TRUST_FAILURE",
    "APPROVAL_FAILURE",
    "VERIFICATION_FAILURE",
]

FAILURE_ACTIONS = [
    "retry",
    "fallback",
    "halt",
    "escalate",
    "rollback",
    "quarantine",
    "dead_letter",
]

FAILURE_RECOMMENDED_ACTION: dict[str, str] = {
    "SKILL_FAILURE": "retry",
    "AGENT_FAILURE": "halt",
    "ORCHESTRATION_FAILURE": "halt",
    "MEMORY_FAILURE": "quarantine",
    "GOVERNANCE_FAILURE": "halt",
    "SECURITY_FAILURE": "halt",
    "CASCADE_FAILURE": "dead_letter",
    "DATA_SOURCE_FAILURE": "halt",
    "REPORT_GENERATION_FAILURE": "retry",
    "FORECASTING_FAILURE": "halt",
    "CHECKPOINT_FAILURE": "rollback",
    "ROLLBACK_FAILURE": "dead_letter",
    "QUARANTINE_FAILURE": "quarantine",
    "COST_FAILURE": "halt",
    "TRUST_FAILURE": "halt",
    "APPROVAL_FAILURE": "escalate",
    "VERIFICATION_FAILURE": "escalate",
}

FAILURE_SEVERITY: dict[str, str] = {
    "SECURITY_FAILURE": "critical",
    "CASCADE_FAILURE": "critical",
    "ROLLBACK_FAILURE": "high",
    "GOVERNANCE_FAILURE": "high",
    "COST_FAILURE": "medium",
    "TRUST_FAILURE": "high",
    "APPROVAL_FAILURE": "medium",
    "VERIFICATION_FAILURE": "medium",
    "MEMORY_FAILURE": "medium",
    "QUARANTINE_FAILURE": "medium",
}


def recommended_action(failure_class: str) -> str:
    """Return the recommended recovery action for a failure class."""
    return FAILURE_RECOMMENDED_ACTION.get(failure_class, "halt")


def incident_severity(failure_class: str) -> str:
    """Return incident severity for a failure class."""
    return FAILURE_SEVERITY.get(failure_class, "medium")
