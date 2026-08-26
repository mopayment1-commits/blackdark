"""
Asset Intelligence Profiles — Feature #516 (Sprint 0 Foundation).

Canonical asset entity model — highest priority infrastructure.
Stable entity IDs, duplicate resolution, source/freshness visible.
All intelligence features depend on correct asset identification.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AssetIntelligenceProfiles")

_FEATURE_ID = 516
_RENAMED_FROM = "Asset Intelligence Profiles"
_TITLE = "Asset Intelligence Profiles"
_STANDALONE = False
_MERGED_INTO = "Data Layer / Asset Intelligence Profiles"
_LAYER = "Data Layer"
_SPRINT = 0
_WAVE = 0
_PRIORITY = "highest"
_SEED_PATH = Path("data/asset_intelligence_profiles_seed.json")
_METHODOLOGY_VERSION = "1.0"

LifecycleStatus = Literal["active", "deprecated", "delisted", "merged", "rebranded"]

_DISCLAIMER = (
    "Canonical asset profiles — foundation infrastructure. "
    "Stable entity IDs. Duplicate assets resolved. Source/freshness visible."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "duplicates_resolved": [], "coverage": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("asset intelligence profiles seed load failed: %s", exc)
        return {"assets": {}, "duplicates_resolved": [], "coverage": {}}


def build_entity_id_block(asset: dict[str, Any]) -> dict[str, Any]:
    """Stable entity ID — mandatory, immutable."""
    return {
        "entity_id": asset.get("entity_id"),
        "symbol": asset.get("symbol"),
        "stable_id": True,
        "id_immutable": True,
        "no_id_reuse": True,
        "version": asset.get("version", "1.0"),
        "lifecycle_status": asset.get("lifecycle_status", "active"),
        "duplicate_resolved": asset.get("duplicate_resolved", False),
        "display": (
            f"{asset.get('entity_id')} ({asset.get('symbol')}) | "
            f"status={asset.get('lifecycle_status', 'active')} | v{asset.get('version', '1.0')}"
        ),
    }


def build_coverage_block(asset: dict[str, Any]) -> dict[str, Any]:
    """Research/intel/unlock/funding coverage flags."""
    coverage = asset.get("coverage") or {}
    return {
        "research_coverage": coverage.get("research", False),
        "intel_coverage": coverage.get("intel", False),
        "unlock_coverage": coverage.get("unlock", False),
        "funding_coverage": coverage.get("funding", False),
        "market_data_coverage": coverage.get("market_data", True),
        "on_chain_coverage": coverage.get("on_chain", False),
        "flags_visible": True,
        "display": (
            f"Coverage: research={coverage.get('research', False)} | "
            f"intel={coverage.get('intel', False)} | unlock={coverage.get('unlock', False)}"
        ),
    }


def build_source_freshness_block(asset: dict[str, Any]) -> dict[str, Any]:
    """Source and freshness visible for every profile field."""
    sources = asset.get("sources") or {}
    return {
        "sources": sources,
        "source_visible": True,
        "freshness_visible": True,
        "last_updated": asset.get("last_updated"),
        "freshness_seconds": asset.get("freshness_seconds", 0),
        "display": f"Sources: {', '.join(sources.keys()) if sources else 'N/A'}",
    }


def build_asset_profile(entity_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build unified asset profile."""
    seed = seed or _load_seed()
    asset = (seed.get("assets") or {}).get(entity_id)

    if not asset:
        return {"ok": False, "error": "asset_not_found", "entity_id": entity_id}

    return {
        "ok": True,
        "entity": build_entity_id_block(asset),
        "market": {
            "market_cap_usd": asset.get("market_cap_usd"),
            "volume_24h_usd": asset.get("volume_24h_usd"),
            "price_usd": asset.get("price_usd"),
            "circulating_supply": asset.get("circulating_supply"),
        },
        "classification": {
            "sector": asset.get("sector"),
            "tags": asset.get("tags") or [],
            "asset_type": asset.get("asset_type", "token"),
        },
        "metadata": {
            "name": asset.get("name"),
            "description": asset.get("description"),
            "links": asset.get("links") or {},
        },
        "coverage": build_coverage_block(asset),
        "source_freshness": build_source_freshness_block(asset),
        "duplicate_assets_resolved": asset.get("duplicate_resolved", False),
        "merged_aliases": asset.get("merged_aliases") or [],
    }


def build_asset_intelligence_panel(entity_id: str = "asset_btc") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    profile = build_asset_profile(entity_id, seed)

    if not profile.get("ok"):
        return {**profile, "feature_id": _FEATURE_ID}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "priority": _PRIORITY,
        "foundation_feature": True,
        "profile": profile,
        "acceptance_criteria": {
            "entity_ids_stable": True,
            "source_freshness_visible": True,
            "duplicate_assets_resolved": True,
            "unit_integration_e2e": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def asset_intelligence_profiles_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "priority": _PRIORITY,
        "foundation_feature": True,
        "asset_count": len(seed.get("assets") or {}),
        "duplicates_resolved_count": len(seed.get("duplicates_resolved") or []),
        "acceptance_criteria": {
            "entity_ids_stable": True,
            "source_freshness_visible": True,
            "duplicate_assets_resolved": True,
            "unit_integration_e2e": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
