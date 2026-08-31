"""CAP978 catalog — official 978-capability scope (646 base + 332 extension).

Scope tiers (contiguous IDs, no gaps or renumbering):
- **978 (full catalog / ``--full`` gate):** IDs 1–978 — institutional closure baseline
  (``Project_978_Capabilities_Grouped_*.pdf``).
- **826 (agreed project / import scope):** IDs 1–826 — 646 base + extension 647–826 (180 rows).
  Delivery batches and ``capabilities-826-import`` target this tier.
- **678 (CI sample / ``sample=True``):** IDs 1–646 + 647–678 (32 extension rows) — fast structural gate.

The 152 IDs **827–978** are real ``extension_647_978`` catalog rows (track T19), not numbering
errors or duplicates. They are **outside the 826 delivery scope by design** but included in the
978 institutional baseline and full-mode gate.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_CATALOG = _ROOT / "docs" / "cap978" / "CAP978_CATALOG.json"

# Official catalog bounds (contiguous 1..978).
CATALOG_TOTAL = 978
BASE_SCOPE_MAX_ID = 646
EXTENSION_SCOPE_MIN_ID = 647
EXTENSION_SCOPE_MAX_ID = 978
EXTENSION_TOTAL = 332

# Agreed project delivery scope (646 + extension 647..826).
PROJECT_SCOPE_TOTAL = 826
PROJECT_EXTENSION_MAX_ID = 826
PROJECT_EXTENSION_TOTAL = 180

# Post-project extension reserved in full catalog only (827..978).
POST_PROJECT_EXTENSION_MIN_ID = 827
POST_PROJECT_EXTENSION_TOTAL = 152

# CI sample structural gate (646 + extension 647..678).
CI_SAMPLE_TOTAL = 678
CI_SAMPLE_EXTENSION_MAX_ID = 678
CI_SAMPLE_EXTENSION_TOTAL = 32

# Reuse cap646 duplicate/external/canonical maps for base scope
from cap646.catalog import (  # noqa: E402
    EXTERNAL_IDS,
    REPEAT_CANONICAL,
    canonical_id as _canonical_id_base,
    is_duplicate as _is_duplicate_base,
    is_external as _is_external_base,
    matrix_by_id,
)

from bd_platform.free_tier_capabilities import FREE_TIER_EXTENSION_IDS  # noqa: E402

EXTENSION_EXTERNAL_IDS: frozenset[int] = FREE_TIER_EXTENSION_IDS | frozenset({649, 658})

# Extension duplicates of base canonical capabilities (same goal/behavior)
EXTENSION_CANONICAL: dict[str, int] = {
    "Smart Alerts": 17,
    "API Data Platform": 103,
    "Watchlists": 214,
    "Data Quality & Provenance Layer": 63,
    "Cross-Domain Decision Intelligence": 251,
    "Signal Registry": 637,
}


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    return json.loads(_CATALOG.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def catalog_by_id() -> dict[int, dict[str, Any]]:
    return {int(r["id"]): r for r in load_catalog()}


def is_extension(capability_id: int) -> bool:
    return capability_id >= 647


def is_external(capability_id: int) -> bool:
    from bd_platform.free_tier_capabilities import FREE_TIER_CAP_IDS

    if capability_id in FREE_TIER_CAP_IDS:
        return False
    if capability_id == 658:
        try:
            from bigquery_export import bigquery_live_ready

            return not bigquery_live_ready()
        except Exception:
            return True
    if capability_id == 649:
        try:
            from dbt_connector import dbt_live_ready

            return not dbt_live_ready()
        except Exception:
            return True
    if capability_id in EXTENSION_EXTERNAL_IDS:
        return True
    if capability_id <= 646:
        return _is_external_base(capability_id)
    return False


def is_duplicate(capability_id: int) -> bool:
    if capability_id <= 646:
        return _is_duplicate_base(capability_id)
    row = catalog_by_id().get(capability_id, {})
    name = row.get("capability", "")
    if name in EXTENSION_CANONICAL:
        return True
    return False


def canonical_id(capability_id: int) -> int:
    if capability_id <= 646:
        return _canonical_id_base(capability_id)
    row = catalog_by_id().get(capability_id, {})
    canon = EXTENSION_CANONICAL.get(row.get("capability", ""))
    return canon if canon else capability_id
