"""CAP978 catalog — official 978-capability scope (646 base + 332 extension)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_CATALOG = _ROOT / "docs" / "cap978" / "CAP978_CATALOG.json"

# Reuse cap646 duplicate/external/canonical maps for base scope
from cap646.catalog import (  # noqa: E402
    EXTERNAL_IDS,
    REPEAT_CANONICAL,
    canonical_id as _canonical_id_base,
    is_duplicate as _is_duplicate_base,
    is_external as _is_external_base,
    matrix_by_id,
)

# Extension capabilities blocked on external vendor/data rights
EXTENSION_EXTERNAL_IDS: frozenset[int] = frozenset(
    {
        647,  # Real-Time Feed — low-latency vendor SLA
        648,  # Datashare — institutional datashare connector
        # 649 dbt — dynamic via dbt_live_ready()
        652,  # BI Connectors — Tableau/Looker external
        672,  # Chainalysis integration — paid vendor
        673,  # Elliptic integration — paid vendor
        674,  # TRM Labs integration — paid vendor
        675,  # Nansen full API — paid vendor
        676,  # Arkham full API — paid vendor
        690,  # Bloomberg Terminal bridge — external license
        691,  # Refinitiv Eikon bridge — external license
        702,  # Kaiko institutional — paid vendor
        703,  # Amberdata institutional — paid vendor
        704,  # CryptoQuant full — paid vendor
        705,  # Glassnode full tier — paid vendor
    }
)

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
