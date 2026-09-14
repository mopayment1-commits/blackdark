"""Historical depth registry per domain/methodology."""

from __future__ import annotations

from typing import Any

HISTORICAL_DEPTH_REGISTRY: dict[str, dict[str, Any]] = {
    "net_edge": {
        "minimum_history_days": 30,
        "preferred_history_days": 365,
        "sampling_frequency": "1m",
        "grade_suitable": True,
        "simulation_suitable": True,
        "earliest_available": "2024-01-01",
        "gaps": [],
    },
    "execution_feasibility": {
        "minimum_history_days": 7,
        "preferred_history_days": 90,
        "requires_l2": True,
        "grade_suitable": True,
        "simulation_suitable": False,
        "earliest_available": "2024-06-01",
        "gaps": ["l2_depth_limited_pre_capture"],
    },
    "evidence_grade": {
        "minimum_history_days": 14,
        "preferred_history_days": 180,
        "grade_suitable": True,
        "simulation_suitable": True,
        "earliest_available": "2024-01-01",
        "gaps": [],
    },
    "macro_regime": {
        "minimum_history_days": 365,
        "preferred_history_days": 3650,
        "grade_suitable": True,
        "simulation_suitable": True,
        "earliest_available": "1990-01-01",
        "source": "fred",
        "gaps": [],
    },
}


def query_historical_depth(methodology_id: str) -> dict[str, Any]:
    entry = HISTORICAL_DEPTH_REGISTRY.get(methodology_id, {})
    return {"methodology_id": methodology_id, **entry}


def check_historical_sufficiency(methodology_id: str, available_days: int | None = None) -> dict[str, Any]:
    entry = query_historical_depth(methodology_id)
    min_days = int(entry.get("minimum_history_days") or 0)
    avail = available_days if available_days is not None else int(entry.get("preferred_history_days") or min_days)
    sufficient = avail >= min_days
    return {
        "methodology_id": methodology_id,
        "available_days": avail,
        "minimum_required_days": min_days,
        "sufficient": sufficient,
        "grade_allowed": sufficient and entry.get("grade_suitable", False),
        "simulation_allowed": sufficient and entry.get("simulation_suitable", False),
    }


def attach_historical_depth(payload: dict[str, Any], *, methodology_id: str = "net_edge") -> dict[str, Any]:
    out = dict(payload)
    check = check_historical_sufficiency(methodology_id)
    out["historical_depth"] = {**query_historical_depth(methodology_id), **check}
    return out
