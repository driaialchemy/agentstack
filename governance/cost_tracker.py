"""Synthetic cost governance for Phase 6 demo workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from skills.skill_registry import get_skill_by_id

DEFAULT_RUN_BUDGET = 100.0
NEAR_LIMIT_RATIO = 0.85

COST_STATUSES = ["within_budget", "near_limit", "exceeded"]


@dataclass
class CostGateResult:
    passed: bool
    cost_status: str
    estimated_skill_cost: float
    run_total_cost: float
    run_budget: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def skill_cost_metadata(skill_id: str, registry_path=None) -> dict[str, Any]:
    skill = get_skill_by_id(skill_id, registry_path)
    if skill is None:
        return {"estimated_cost": 0.0, "cost_category": "unknown", "cost_budget_impact": "low"}
    return {
        "estimated_cost": float(skill.get("estimated_cost", 1.0)),
        "cost_category": str(skill.get("cost_category", "compute")),
        "cost_budget_impact": str(skill.get("cost_budget_impact", "low")),
    }


def estimate_skill_cost(skill_id: str, registry_path=None) -> float:
    return float(skill_cost_metadata(skill_id, registry_path)["estimated_cost"])


class CostTracker:
    """Track synthetic estimated costs per run."""

    def __init__(self, run_budget: float = DEFAULT_RUN_BUDGET):
        self.run_budget = float(run_budget)
        self._run_costs: dict[str, float] = {}
        self._skill_calls: dict[str, list[dict[str, Any]]] = {}

    def reset_run(self, run_id: str) -> None:
        self._run_costs[run_id] = 0.0
        self._skill_calls[run_id] = []

    def record_skill_call(
        self,
        *,
        run_id: str,
        skill_id: str,
        registry_path=None,
    ) -> dict[str, Any]:
        if run_id not in self._run_costs:
            self.reset_run(run_id)
        meta = skill_cost_metadata(skill_id, registry_path)
        cost = float(meta["estimated_cost"])
        self._run_costs[run_id] += cost
        entry = {
            "skill_id": skill_id,
            "estimated_cost": cost,
            "cost_category": meta["cost_category"],
            "cost_budget_impact": meta["cost_budget_impact"],
            "run_total_cost": self._run_costs[run_id],
        }
        self._skill_calls[run_id].append(entry)
        return entry

    def run_total(self, run_id: str) -> float:
        return float(self._run_costs.get(run_id, 0.0))

    def cost_status(self, run_id: str) -> str:
        total = self.run_total(run_id)
        if total > self.run_budget:
            return "exceeded"
        if total >= self.run_budget * NEAR_LIMIT_RATIO:
            return "near_limit"
        return "within_budget"

    def evaluate_skill_call(
        self,
        *,
        run_id: str,
        skill_id: str,
        registry_path=None,
        include_pending: bool = True,
    ) -> CostGateResult:
        pending = estimate_skill_cost(skill_id, registry_path) if include_pending else 0.0
        current = self.run_total(run_id)
        projected = current + pending
        status = "within_budget"
        if projected > self.run_budget:
            status = "exceeded"
        elif projected >= self.run_budget * NEAR_LIMIT_RATIO:
            status = "near_limit"

        passed = status != "exceeded"
        reason = (
            f"Projected run cost {projected:.2f} / budget {self.run_budget:.2f} ({status})."
        )
        return CostGateResult(
            passed=passed,
            cost_status=status,
            estimated_skill_cost=pending,
            run_total_cost=current,
            run_budget=self.run_budget,
            reason=reason,
        )

    def skill_calls_for_run(self, run_id: str) -> list[dict[str, Any]]:
        return list(self._skill_calls.get(run_id, []))

    def summary(self, run_id: str) -> dict[str, Any]:
        return {
            "run_id": run_id,
            "run_budget": self.run_budget,
            "run_total_cost": self.run_total(run_id),
            "cost_status": self.cost_status(run_id),
            "skill_calls": self.skill_calls_for_run(run_id),
        }
