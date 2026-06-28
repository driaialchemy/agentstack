"""Synthetic document database for Phase 1 demos."""

from __future__ import annotations

from typing import Any

SYNTHETIC_DOCUMENTS: list[dict[str, Any]] = [
    {
        "doc_id": "DOC-001",
        "title": "Master Services Agreement — Acme Corp",
        "doc_type": "contract",
        "risk_tier": "medium",
        "summary": "Standard MSA with liability cap and 30-day termination notice.",
        "excerpt": "Provider liability shall not exceed fees paid in the prior twelve months.",
    },
    {
        "doc_id": "DOC-002",
        "title": "Data Processing Addendum — Beta Analytics",
        "doc_type": "compliance",
        "risk_tier": "high",
        "summary": "DPA covering subprocessors, breach notification, and audit rights.",
        "excerpt": "Controller may audit processing activities upon 30 days written notice.",
    },
    {
        "doc_id": "DOC-003",
        "title": "Statement of Work — Cloud Migration",
        "doc_type": "sow",
        "risk_tier": "low",
        "summary": "Fixed-scope migration with milestone payments and acceptance criteria.",
        "excerpt": "Deliverables are accepted when validation tests pass in staging.",
    },
    {
        "doc_id": "DOC-004",
        "title": "Vendor Security Questionnaire Response",
        "doc_type": "assessment",
        "risk_tier": "medium",
        "summary": "Self-attested controls for encryption, access management, and logging.",
        "excerpt": "Data at rest is encrypted using AES-256 across production systems.",
    },
]


def get_documents() -> list[dict[str, Any]]:
    """Return a copy of synthetic documents."""
    return [dict(document) for document in SYNTHETIC_DOCUMENTS]


def summarize_documents() -> dict[str, Any]:
    """Produce a simple summary for the demo workflow."""
    documents = get_documents()
    risk_counts: dict[str, int] = {}
    for document in documents:
        tier = document["risk_tier"]
        risk_counts[tier] = risk_counts.get(tier, 0) + 1

    return {
        "document_count": len(documents),
        "doc_types": sorted({document["doc_type"] for document in documents}),
        "risk_counts": risk_counts,
        "highlighted_documents": documents[:2],
    }
