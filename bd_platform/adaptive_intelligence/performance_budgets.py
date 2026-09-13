"""Runtime/Cost/Performance budgets — spec §30 (AIE-020)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PerformanceBudget:
    max_candidates: int = 24
    max_selected: int = 8
    latency_class: str = "interactive"
    max_latency_ms: float = 2000.0
    compute_cost_units: float = 10.0
    cache_policy: str = "reuse_recent"


def check_budget(
    budget: PerformanceBudget,
    *,
    candidate_count: int,
    selected_count: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    if candidate_count > budget.max_candidates:
        raise ValueError("budget_candidate_explosion")
    if selected_count > budget.max_selected:
        raise ValueError("budget_selected_overflow")
    if elapsed_ms > budget.max_latency_ms:
        raise ValueError("budget_latency_exceeded")
    return {
        "within_budget": True,
        "candidate_count": candidate_count,
        "selected_count": selected_count,
        "elapsed_ms": elapsed_ms,
        "latency_class": budget.latency_class,
    }
