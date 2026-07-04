"""Chart generation for Phase 4 analytics demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_revenue_chart(
    *,
    time_series: list[dict[str, Any]],
    output_path: Path,
    forecast: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Save a simple revenue chart PNG and return structured chart metadata."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for chart generation.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    periods = [row["period"] for row in time_series]
    revenues = [row["revenue_usd"] for row in time_series]

    plt.figure(figsize=(8, 4))
    plt.plot(periods, revenues, marker="o", label="Historical revenue")
    if forecast:
        forecast_periods = [point["period"] for point in forecast]
        forecast_values = [point["projected_revenue_usd"] for point in forecast]
        plt.plot(
            forecast_periods,
            forecast_values,
            marker="x",
            linestyle="--",
            label="Projected revenue",
        )
    plt.title("Synthetic Revenue Trend (Demo)")
    plt.xlabel("Period")
    plt.ylabel("Revenue (USD)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, format="png")
    plt.close()

    return {
        "chart_type": "line",
        "chart_path": str(output_path),
        "title": "Synthetic Revenue Trend (Demo)",
        "series": {
            "historical_points": len(time_series),
            "forecast_points": len(forecast or []),
        },
    }
