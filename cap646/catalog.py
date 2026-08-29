"""Load frozen CAP646 catalog + gap matrix."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_CATALOG = _ROOT / "docs" / "cap646" / "CAP646_CATALOG.json"
_MATRIX = _ROOT / "docs" / "cap646" / "CAP646_GAP_MATRIX.json"

REPEAT_CANONICAL: dict[str, int] = {
    "Data Quality & Provenance Layer": 63,
    "Metric Methodology Registry": 64,
    "Cross-Domain Decision Intelligence Layer": 69,
    "Cross-Domain Decision Intelligence": 251,
    "Smart Alerts": 17,
    "Funding Rate Intelligence": 86,
    "Open Interest Intelligence": 205,
    "Liquidation Intelligence": 88,
    "API Data Platform": 103,
    "Futures Open Interest Intelligence": 85,
    "Futures Volume Intelligence": 126,
    "Sentiment Intelligence": 129,
    "Watchlists": 214,
    "Long/Short Ratio Intelligence": 235,
    "Liquidation Heatmap": 252,
    "Options Volume": 263,
    "Transaction Search": 279,
    "Reference Rates": 330,
    "TVL Intelligence": 354,
    "DEX Volume": 356,
}

# Vendor-blocked IDs tracked in free_tier_capabilities + matrix classification — not closure registry.
EXTERNAL_IDS: frozenset[int] = frozenset()


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    return json.loads(_CATALOG.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_matrix_rows() -> list[dict[str, Any]]:
    data = json.loads(_MATRIX.read_text(encoding="utf-8"))
    return data["rows"]


@lru_cache(maxsize=1)
def catalog_by_id() -> dict[int, dict[str, Any]]:
    return {int(r["id"]): r for r in load_catalog()}


@lru_cache(maxsize=1)
def matrix_by_id() -> dict[int, dict[str, Any]]:
    return {int(r["id"]): r for r in load_matrix_rows()}


def canonical_id(capability_id: int) -> int:
    row = catalog_by_id()[capability_id]
    canon = REPEAT_CANONICAL.get(row["capability"])
    return canon if canon and canon != capability_id else capability_id


def is_external(capability_id: int) -> bool:
    if capability_id not in EXTERNAL_IDS:
        return False
    try:
        from bd_platform.free_tier_capabilities import FREE_TIER_BASE_IDS

        if capability_id in FREE_TIER_BASE_IDS:
            return False
    except Exception:
        pass
    return True


def is_duplicate(capability_id: int) -> bool:
    row = matrix_by_id().get(capability_id, {})
    return row.get("final_classification") == "DUPLICATE/ALREADY_COVERED"
