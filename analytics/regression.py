"""Simple linear regression for synthetic analytics demos."""

from __future__ import annotations

from typing import Any


def run_regression(*, time_series: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit a simple linear regression of revenue on period index."""
    if len(time_series) < 2:
        raise ValueError("At least two time-series points are required for regression.")

    target_variable = "revenue_usd"
    feature_variables = ["period"]
    xs = [float(row["period"]) for row in time_series]
    ys = [float(row[target_variable]) for row in time_series]
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("Regression feature has zero variance.")

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    predictions = [intercept + slope * x for x in xs]
    ss_res = sum((y - y_hat) ** 2 for y, y_hat in zip(ys, predictions))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot else 0.0

    interpretation = (
        f"Revenue increases by about ${slope:,.0f} per period in this synthetic demo series "
        f"(R-squared={r_squared:.2f}). This is a simple linear fit for demonstration, not a "
        "production forecasting model."
    )
    limitations = [
        "Synthetic demo data only.",
        "Single-feature linear model; real drivers are not modeled.",
        "Do not use for business decisions.",
    ]

    return {
        "target_variable": target_variable,
        "feature_variables": feature_variables,
        "coefficients": {
            "intercept": round(intercept, 2),
            "period_slope": round(slope, 2),
        },
        "r_squared": round(r_squared, 4),
        "interpretation": interpretation,
        "limitations": limitations,
    }
