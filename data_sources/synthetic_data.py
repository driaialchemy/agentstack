"""Synthetic structured database for Phase 1 demos."""

from __future__ import annotations

from typing import Any

SYNTHETIC_RECORDS: list[dict[str, Any]] = [
    {
        "id": 1,
        "region": "North",
        "quarter": "Q1",
        "category": "Software",
        "revenue_usd": 125000,
        "units_sold": 420,
    },
    {
        "id": 2,
        "region": "South",
        "quarter": "Q1",
        "category": "Services",
        "revenue_usd": 98000,
        "units_sold": 310,
    },
    {
        "id": 3,
        "region": "East",
        "quarter": "Q2",
        "category": "Software",
        "revenue_usd": 142500,
        "units_sold": 465,
    },
    {
        "id": 4,
        "region": "West",
        "quarter": "Q2",
        "category": "Hardware",
        "revenue_usd": 87000,
        "units_sold": 190,
    },
    {
        "id": 5,
        "region": "North",
        "quarter": "Q3",
        "category": "Services",
        "revenue_usd": 111200,
        "units_sold": 355,
    },
]


def get_structured_records() -> list[dict[str, Any]]:
    """Return a copy of synthetic structured records."""
    return [dict(record) for record in SYNTHETIC_RECORDS]


def summarize_structured_data() -> dict[str, Any]:
    """Produce a simple summary for the demo workflow."""
    records = get_structured_records()
    total_revenue = sum(record["revenue_usd"] for record in records)
    regions = sorted({record["region"] for record in records})
    categories = sorted({record["category"] for record in records})

    return {
        "record_count": len(records),
        "total_revenue_usd": total_revenue,
        "average_revenue_usd": round(total_revenue / len(records), 2),
        "regions": regions,
        "categories": categories,
        "sample_records": records[:3],
    }
