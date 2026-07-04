"""Fourier-style seasonality projection demo."""

from __future__ import annotations

import math
from typing import Any


def run_fourier_forecast(*, time_series: list[dict[str, Any]], horizon: int = 3) -> dict[str, Any]:
    """Project future values using a simple cyclical (Fourier-style) demo model."""
    if len(time_series) < 4:
        raise ValueError("At least four time-series points are required for forecast demo.")

    values = [float(row["revenue_usd"]) for row in time_series]
    periods = [float(row["period"]) for row in time_series]
    mean_value = sum(values) / len(values)
    amplitude = (max(values) - min(values)) / 2 if values else 0.0
    seasonal_period = 12.0

    seasonal_components = [
        {
            "component": "sin",
            "period": seasonal_period,
            "weight": round(amplitude * 0.6, 2),
        },
        {
            "component": "cos",
            "period": seasonal_period / 2,
            "weight": round(amplitude * 0.3, 2),
        },
    ]

    last_period = periods[-1]
    projected: list[dict[str, Any]] = []
    for step in range(1, horizon + 1):
        future_period = last_period + step
        seasonal_adjustment = sum(
            comp["weight"]
            * math.sin(2 * math.pi * future_period / comp["period"])
            for comp in seasonal_components
            if comp["component"] == "sin"
        )
        seasonal_adjustment += sum(
            comp["weight"]
            * math.cos(2 * math.pi * future_period / comp["period"])
            for comp in seasonal_components
            if comp["component"] == "cos"
        )
        projected_value = round(mean_value + seasonal_adjustment, 2)
        projected.append(
            {
                "period": int(future_period),
                "projected_revenue_usd": projected_value,
            }
        )

    limitation_note = (
        "This Fourier-style projection demonstrates seasonality and cyclical patterns on "
        "synthetic data. It is not guaranteed prediction and must not be treated as a "
        "production forecast."
    )
    interpretation = (
        f"Projected {horizon} future periods using a simple seasonal/cyclical demo model. "
        f"{limitation_note}"
    )

    return {
        "forecast_horizon": horizon,
        "seasonal_components": seasonal_components,
        "projected_values": projected,
        "interpretation": interpretation,
        "limitation_note": limitation_note,
        "limitations": [
            limitation_note,
            "Synthetic demo data only.",
            "Model complexity is intentionally minimal for governance demonstration.",
        ],
    }
