"""Deterministic security checks for Phase 6 demo governance."""

from __future__ import annotations

import re
from typing import Any

SECURITY_RISK_LEVELS = ["none", "low", "medium", "high", "critical"]

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s*:\s*",
    r"<\s*script",
    r"drop\s+table",
]

INSTRUCTION_PATTERNS = [
    r"you\s+must\s+now",
    r"execute\s+the\s+following\s+command",
    r"override\s+governance",
]

PRIVILEGE_PATTERNS = [
    r"grant\s+admin",
    r"escalate\s+privileges",
    r"bypass\s+policy",
    r"disable\s+gates",
]

SENSITIVE_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN-like pattern"),
    (r"\b\d{16}\b", "credit-card-like pattern"),
    (r"api[_-]?key\s*[:=]\s*\S+", "API key pattern"),
]

UNTRUSTED_SOURCE_MARKERS = [
    "untrusted_external_source",
    "external_content_as_instruction",
]


def _find_pattern(text: str, patterns: list[str]) -> str | None:
    lowered = text.lower()
    for pattern in patterns:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return pattern
    return None


def redact_sensitive_text(text: str) -> tuple[str, list[str]]:
    redacted = text
    issues: list[str] = []
    for pattern, label in SENSITIVE_PATTERNS:
        if re.search(pattern, redacted, flags=re.IGNORECASE):
            issues.append(label)
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted, issues


def run_security_check(
    *,
    content: str | dict[str, Any] | None = None,
    source_marker: str | None = None,
    tool_request: str | None = None,
) -> dict[str, Any]:
    """Run simple pattern-based security checks on demo content."""
    if isinstance(content, dict):
        text = " ".join(str(value) for value in content.values())
    else:
        text = str(content or "")

    detected_issue = None
    security_risk_level = "none"
    recommended_action = "allow"
    issue_type = None

    if source_marker in UNTRUSTED_SOURCE_MARKERS:
        detected_issue = f"Untrusted source marker: {source_marker}"
        issue_type = "untrusted_source_marker"
        security_risk_level = "high"
        recommended_action = "block"

    if not detected_issue:
        match = _find_pattern(text, INJECTION_PATTERNS)
        if match:
            detected_issue = f"Prompt injection pattern detected: {match}"
            issue_type = "prompt_injection"
            security_risk_level = "critical"
            recommended_action = "block"

    if not detected_issue:
        match = _find_pattern(text, INSTRUCTION_PATTERNS)
        if match:
            detected_issue = f"External content treated as instruction: {match}"
            issue_type = "external_instruction"
            security_risk_level = "high"
            recommended_action = "block"

    if not detected_issue and tool_request:
        if any(token in tool_request.lower() for token in ("delete_all", "shell_exec", "raw_sql")):
            detected_issue = f"Unsafe tool request: {tool_request}"
            issue_type = "unsafe_tool_request"
            security_risk_level = "high"
            recommended_action = "block"

    if not detected_issue:
        match = _find_pattern(text, PRIVILEGE_PATTERNS)
        if match:
            detected_issue = f"Privilege escalation attempt: {match}"
            issue_type = "privilege_escalation"
            security_risk_level = "critical"
            recommended_action = "block"

    redacted_output, sensitive_issues = redact_sensitive_text(text)
    if sensitive_issues and not detected_issue:
        detected_issue = f"Sensitive data pattern(s): {', '.join(sensitive_issues)}"
        issue_type = "sensitive_data_pattern"
        security_risk_level = "medium"
        recommended_action = "redact"

    passed = security_risk_level in {"none", "low", "medium"} and recommended_action != "block"
    if security_risk_level == "medium" and sensitive_issues:
        passed = True

    return {
        "passed": passed,
        "security_risk_level": security_risk_level,
        "detected_issue": detected_issue,
        "issue_type": issue_type,
        "recommended_action": recommended_action,
        "redacted_output": redacted_output if sensitive_issues else text,
        "sensitive_patterns": sensitive_issues,
    }
