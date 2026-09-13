"""SLA / internal SLO registry (DIG-013, DIG-014, DIG-024)."""

from __future__ import annotations

from typing import Any

_FRESHNESS_CLASSES = {
    "T0": 5,
    "T1": 30,
    "T2": 60,
    "T3": 300,
    "T4": 900,
    "T5": 3600,
    "T6": 86400,
}


def freshness_class_max_age(class_id: str) -> float:
    return float(_FRESHNESS_CLASSES.get(class_id, 300))


def slo_status(source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "freshness_class": "T3",
        "max_age_seconds": freshness_class_max_age("T3"),
        "internal_slo_met": True,
    }
