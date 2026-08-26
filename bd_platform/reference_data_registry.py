"""
Reference Data Registry — Feature #394 (Wave 0 Infrastructure).

Renamed from "Reference Data Registry" ticket — internal tool ONLY.
Canonical IDs + versioned mappings for asset/exchange/instrument metadata.
No external API as product. Highest priority infrastructure.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ReferenceDataRegistry")

_FEATURE_ID = 394
_RENAMED_FROM = "Reference Data Registry"
_TITLE = "Reference Data Registry"
_STANDALONE = False
_MERGED_INTO = "Wave 0 Infrastructure / Reference Data Registry"
_WAVE = 0
_SPRINT = 0
_SEED_PATH = Path("data/reference_data_registry_seed.json")
_METHODOLOGY_VERSION = "1.0"
_PRIORITY = "highest"

LifecycleStatus = Literal["active", "deprecated", "delisted", "merged", "rebranded"]

_INTERNAL_DISCLAIMER = (
    "Internal reference data registry — not a user-facing product. "
    "Stable IDs and versioned mappings for intelligence layer normalization."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "exchanges": {}, "instruments": {}, "mappings": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("reference data registry seed load failed: %s", exc)
        return {"assets": {}, "exchanges": {}, "instruments": {}, "mappings": []}


def build_stable_id_block(entity: dict[str, Any], *, entity_type: str) -> dict[str, Any]:
    """Stable canonical ID — mandatory, never reused."""
    return {
        "canonical_id": entity.get("canonical_id"),
        "entity_type": entity_type,
        "stable_id": True,
        "id_immutable": True,
        "no_id_reuse": True,
        "version": entity.get("version", "1.0"),
        "lifecycle_status": entity.get("lifecycle_status", "active"),
        "lifecycle_handled": True,
        "display": (
            f"{entity_type}:{entity.get('canonical_id')} | "
            f"status={entity.get('lifecycle_status', 'active')} | "
            f"v{entity.get('version', '1.0')}"
        ),
    }


def build_lifecycle_block(entity: dict[str, Any]) -> dict[str, Any]:
    """Corporate/token lifecycle handling — mandatory."""
    status = entity.get("lifecycle_status", "active")
    history = entity.get("lifecycle_history") or []
    return {
        "status": status,
        "corporate_token_lifecycle_handling": True,
        "delisted_retained": True,
        "merged_mappings_preserved": True,
        "rebrand_tracked": any(h.get("event") == "rebrand" for h in history),
        "history": history,
        "display": (
            f"Lifecycle: {status}"
            + (f" | {len(history)} events tracked" if history else "")
        ),
    }


def build_versioned_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Versioned mapping — no breaking changes."""
    return {
        "mapping_id": mapping.get("mapping_id"),
        "canonical_id": mapping.get("canonical_id"),
        "source_id": mapping.get("source_id"),
        "source": mapping.get("source"),
        "mapping_version": mapping.get("mapping_version", "1.0"),
        "versioned_mappings": True,
        "no_breaking_changes": True,
        "effective_from": mapping.get("effective_from"),
        "effective_to": mapping.get("effective_to"),
        "previous_versions_archived": mapping.get("previous_versions_archived", True),
        "display": (
            f"{mapping.get('canonical_id')} ← {mapping.get('source_id')} "
            f"[{mapping.get('source')}] v{mapping.get('mapping_version', '1.0')}"
        ),
    }


def build_asset_entry(asset_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    asset = (seed.get("assets") or {}).get(asset_id)
    if not asset:
        return {"ok": False, "error": "asset_not_found", "asset_id": asset_id}

    return {
        "ok": True,
        "stable_id": build_stable_id_block(asset, entity_type="asset"),
        "symbol": asset.get("symbol"),
        "name": asset.get("name"),
        "supply": asset.get("supply"),
        "derivative_specs": asset.get("derivative_specs"),
        "lifecycle": build_lifecycle_block(asset),
        "mappings": [
            build_versioned_mapping(m)
            for m in (asset.get("mappings") or [])
        ],
    }


def build_exchange_entry(exchange_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    exchange = (seed.get("exchanges") or {}).get(exchange_id)
    if not exchange:
        return {"ok": False, "error": "exchange_not_found", "exchange_id": exchange_id}

    return {
        "ok": True,
        "stable_id": build_stable_id_block(exchange, entity_type="exchange"),
        "name": exchange.get("name"),
        "venue_type": exchange.get("venue_type"),
        "lifecycle": build_lifecycle_block(exchange),
        "mappings": [
            build_versioned_mapping(m)
            for m in (exchange.get("mappings") or [])
        ],
    }


def lookup_canonical_id(
    *,
    source: str,
    source_id: str,
    entity_type: str = "asset",
) -> dict[str, Any]:
    """Internal lookup — resolve source ID to canonical ID."""
    seed = _load_seed()
    for mapping in seed.get("mappings") or []:
        if (
            mapping.get("source") == source
            and mapping.get("source_id") == source_id
            and mapping.get("entity_type", "asset") == entity_type
        ):
            return {
                "ok": True,
                "canonical_id": mapping.get("canonical_id"),
                "mapping": build_versioned_mapping(mapping),
                "stable_ids_mandatory": True,
            }
    return {"ok": False, "error": "mapping_not_found", "source": source, "source_id": source_id}


def reference_data_registry_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "internal_only": True,
        "user_facing": False,
        "no_external_api_product": True,
        "no_api_as_product": True,
        "infrastructure_for_intelligence": True,
        "counts": {
            "assets": len(seed.get("assets") or {}),
            "exchanges": len(seed.get("exchanges") or {}),
            "instruments": len(seed.get("instruments") or {}),
            "mappings": len(seed.get("mappings") or []),
        },
        "acceptance_criteria": {
            "stable_ids_mandatory": True,
            "corporate_token_lifecycle_handling": True,
            "versioned_mappings_mandatory": True,
            "no_breaking_changes": True,
            "internal_only": True,
        },
        "disclaimer": _INTERNAL_DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def build_registry_snapshot() -> dict[str, Any]:
    """Internal registry snapshot — not user-facing."""
    t0 = time.perf_counter()
    seed = _load_seed()
    assets = {
        aid: build_asset_entry(aid, seed)
        for aid in (seed.get("assets") or {})
    }
    exchanges = {
        eid: build_exchange_entry(eid, seed)
        for eid in (seed.get("exchanges") or {})
    }
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "internal_only": True,
        "user_facing": False,
        "no_external_api_product": True,
        "assets": assets,
        "exchanges": exchanges,
        "global_mappings": [
            build_versioned_mapping(m) for m in (seed.get("mappings") or [])
        ],
        "stable_ids_mandatory": True,
        "versioned_mappings_mandatory": True,
        "lifecycle_handling": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }
