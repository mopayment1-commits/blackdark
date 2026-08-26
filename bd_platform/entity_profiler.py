"""
Entity Profiler — Feature #736 Exchange Usage Intelligence absorbed (Sprint 2).

#736 NOT standalone — layer in Entity Intelligence / Entity Profiler.
Exchange labels versioned, internal flows filtered.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.EntityProfiler")

_FEATURE_ID = 736
_ABSORBED_IDS = (736,)
_STANDALONE = False
_MERGED_INTO = "Entity Intelligence / Entity Profiler"
_SPRINT = 2
_SEED_PATH = Path("data/entity_profiler_seed.json")
_METHODOLOGY_VERSION = "1.0"
_LABELS_VERSION = "1.0"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"entities": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("entity profiler seed load failed: %s", exc)
        return {"entities": {}}


def build_exchange_labels_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    labels = seed.get("exchange_labels") or {}
    return {
        "version": labels.get("version", _LABELS_VERSION),
        "last_updated": labels.get("last_updated"),
        "versioned": True,
        "internal_flows_filtered": True,
        "display": f"Exchange labels v{labels.get('version', _LABELS_VERSION)} | Internal flows filtered",
    }


def build_exchange_usage_profile(entity_data: dict[str, Any], *, entity_id: str) -> dict[str, Any]:
    venues = entity_data.get("venue_interactions") or []
    filtered = [v for v in venues if not v.get("internal_flow", False)]
    total_volume = sum(float(v.get("volume_usd", 0)) for v in filtered)

    by_venue: dict[str, float] = {}
    for v in filtered:
        venue = v.get("venue", "unknown")
        by_venue[venue] = by_venue.get(venue, 0) + float(v.get("volume_usd", 0))

    ranked = sorted(by_venue.items(), key=lambda x: x[1], reverse=True)
    return {
        "sub_task": "#736",
        "entity_id": entity_id,
        "venue_count": len(ranked),
        "total_volume_usd": round(total_volume, 2),
        "top_venues": [{"venue": v, "volume_usd": vol, "share_pct": round(vol / total_volume * 100, 1) if total_volume else 0} for v, vol in ranked[:5]],
        "internal_flows_excluded": len(venues) - len(filtered),
        "exchange_labels_versioned": True,
        "display": f"Top venue: {ranked[0][0] if ranked else 'N/A'} | {len(filtered)} external interactions",
    }


def build_entity_profiler_panel(entity_id: str = "whale_001") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id)

    if not entity:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "entity_not_found", "entity_id": entity_id}

    usage = build_exchange_usage_profile(entity, entity_id=entity_id)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "entity_id": entity_id,
        "entity_type": entity.get("entity_type"),
        "exchange_usage": usage,
        "exchange_labels": build_exchange_labels_block(seed),
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def entity_profiler_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Entity Profiler",
        "absorbed_tickets": {736: "Exchange Usage Intelligence"},
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "exchange_labels": build_exchange_labels_block(seed),
        "acceptance_criteria": {
            "exchange_labels_versioned": True,
            "internal_flows_filtered": True,
        },
        "entity_count": len(seed.get("entities") or {}),
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
