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
    {
        "id": 6,
        "region": "South",
        "quarter": "Q3",
        "category": "Software",
        "revenue_usd": 118900,
        "units_sold": 390,
    },
    {
        "id": 7,
        "region": "East",
        "quarter": "Q4",
        "category": "Hardware",
        "revenue_usd": 94000,
        "units_sold": 210,
    },
    {
        "id": 8,
        "region": "West",
        "quarter": "Q4",
        "category": "Services",
        "revenue_usd": 105600,
        "units_sold": 340,
    },
]

# Monthly synthetic time series for Phase 4 analytics (demo only).
MONTHLY_TIME_SERIES: list[dict[str, Any]] = [
    {"period": 1, "month": "Jan", "revenue_usd": 95000, "units_sold": 310},
    {"period": 2, "month": "Feb", "revenue_usd": 98000, "units_sold": 320},
    {"period": 3, "month": "Mar", "revenue_usd": 102000, "units_sold": 335},
    {"period": 4, "month": "Apr", "revenue_usd": 108000, "units_sold": 350},
    {"period": 5, "month": "May", "revenue_usd": 112000, "units_sold": 365},
    {"period": 6, "month": "Jun", "revenue_usd": 115000, "units_sold": 372},
    {"period": 7, "month": "Jul", "revenue_usd": 118000, "units_sold": 380},
    {"period": 8, "month": "Aug", "revenue_usd": 116500, "units_sold": 376},
    {"period": 9, "month": "Sep", "revenue_usd": 120000, "units_sold": 388},
    {"period": 10, "month": "Oct", "revenue_usd": 123000, "units_sold": 395},
    {"period": 11, "month": "Nov", "revenue_usd": 126000, "units_sold": 402},
    {"period": 12, "month": "Dec", "revenue_usd": 129000, "units_sold": 410},
]


def get_structured_records() -> list[dict[str, Any]]:
    """Return a copy of synthetic structured records."""
    return [dict(record) for record in SYNTHETIC_RECORDS]


def get_monthly_time_series() -> list[dict[str, Any]]:
    """Return synthetic monthly records for analytics and forecasting demos."""
    return [dict(record) for record in MONTHLY_TIME_SERIES]


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
