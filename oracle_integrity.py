"""
BLACKDARK — Oracle data integrity guards.

Separates live predictions from synthetic seeded backfill so training,
public metrics, and track records never mix demo data with real performance.
"""

from __future__ import annotations

from typing import Any

SYNTHETIC_PREDICTION_SOURCES: frozenset[str] = frozenset({"historical_seed"})


def prediction_source(row: dict[str, Any]) -> str:
    return str(row.get("source") or "oracle")


def is_synthetic_prediction(row: dict[str, Any]) -> bool:
    return prediction_source(row) in SYNTHETIC_PREDICTION_SOURCES


def filter_live_predictions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not is_synthetic_prediction(row)]


def live_source_sql(*, table_alias: str = "") -> str:
    prefix = f"{table_alias}." if table_alias else ""
    return f"({prefix}source IS NULL OR {prefix}source NOT IN ('historical_seed'))"
