"""Exploratory data analysis for synthetic structured data."""

from __future__ import annotations

from typing import Any


def run_eda(
    *,
    structured_records: list[dict[str, Any]],
    time_series: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return structured EDA output with plain-English interpretation."""
    columns = sorted({key for record in structured_records for key in record.keys()})
    numeric_fields = ["revenue_usd", "units_sold", "id", "period"]
    numeric_summary: dict[str, dict[str, float]] = {}
    missing_values: dict[str, int] = {column: 0 for column in columns}

    for column in columns:
        values = [record.get(column) for record in structured_records]
        missing_values[column] = sum(1 for value in values if value is None)
        if column in numeric_fields or column == "revenue_usd":
            nums = [float(value) for value in values if isinstance(value, (int, float))]
            if nums:
                numeric_summary[column] = {
                    "min": min(nums),
                    "max": max(nums),
                    "mean": round(sum(nums) / len(nums), 2),
                }

    revenues = [float(row["revenue_usd"]) for row in time_series]
    trend_direction = "upward"
    if len(revenues) >= 2 and revenues[-1] < revenues[0]:
        trend_direction = "downward"

    interpretation = (
        f"The synthetic dataset contains {len(structured_records)} structured records "
        f"and {len(time_series)} monthly observations. Revenue shows an {trend_direction} "
        "demo trend across the monthly series. This is synthetic data for governed demonstration only."
    )

    return {
        "row_count": len(structured_records),
        "time_series_count": len(time_series),
        "columns": columns,
        "numeric_summary": numeric_summary,
        "missing_value_summary": missing_values,
        "trend_summary": {
            "direction": trend_direction,
            "first_period_revenue": revenues[0] if revenues else None,
            "last_period_revenue": revenues[-1] if revenues else None,
        },
        "interpretation": interpretation,
    }
