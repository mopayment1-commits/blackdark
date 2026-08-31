"""
Entity Resolution Engine — Feature #541 (Sprint 0 Foundation — Critical).

Cluster addresses into entities with source/confidence/version.
Unknown remains unknown — no AI attribution without evidence.
Foundation for #532, #539, #540, #542, #543, #544–550.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EntityResolutionEngine")

_FEATURE_ID = 541
_TITLE = "Entity Resolution Engine"
_STANDALONE = False
_MERGED_INTO = "Foundation / Entity Resolution Engine"
_LAYER = "Foundation Layer"
_SPRINT = 0
_WAVE = 0
_PRIORITY = "critical"
_SEED_PATH = Path("data/entity_resolution_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"
_CLUSTER_VERSION = "1.0"

ConfidenceLevel = Literal["verified", "high", "medium", "low", "unknown"]

_DISCLAIMER = (
    "Entity resolution infrastructure — source/confidence/version mandatory. "
    "Unknown remains unknown. No attribution without evidence."
)

_BANNED_TERMS = (
    "ai attribution",
    "guessed entity",
    "confirmed owner",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"entities": {}, "clusters": {}, "address_index": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("entity resolution engine seed load failed: %s", exc)
        return {"entities": {}, "clusters": {}, "address_index": {}}


def build_cluster_version_block(cluster: dict[str, Any]) -> dict[str, Any]:
    """Every cluster versioned — auditable historically."""
    return {
        "cluster_id": cluster.get("cluster_id"),
        "cluster_version": cluster.get("version", _CLUSTER_VERSION),
        "versioned": True,
        "auditable_historically": True,
        "effective_from": cluster.get("effective_from"),
        "last_updated": cluster.get("last_updated"),
        "display": f"Cluster {cluster.get('cluster_id')} v{cluster.get('version', _CLUSTER_VERSION)}",
    }


def build_attribution_block(attribution: dict[str, Any]) -> dict[str, Any]:
    """Source/confidence/version mandatory. Unknown remains unknown."""
    confidence = attribution.get("confidence", "unknown")
    source = attribution.get("source")
    label = attribution.get("label")

    if not source or confidence == "unknown" or not label:
        return {
            "entity_label": "Unknown",
            "confidence": "unknown",
            "source": source,
            "unknown_remains_unknown": True,
            "no_guessing": True,
            "no_ai_attribution_without_evidence": True,
            "display": "Entity: Unknown | Confidence: unknown",
        }

    return {
        "entity_label": label,
        "confidence": confidence,
        "source": source,
        "source_mandatory": True,
        "confidence_mandatory": True,
        "version": attribution.get("version", _CLUSTER_VERSION),
        "evidence_refs": attribution.get("evidence_refs") or [],
        "unknown_remains_unknown": False,
        "no_ai_attribution_without_evidence": True,
        "display": f"Entity: {label} | Confidence: {confidence} | Source: {source}",
    }


def resolve_address(address: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve single address to entity cluster."""
    seed = seed or _load_seed()
    addr = address.lower()
    index_entry = (seed.get("address_index") or {}).get(addr)

    if not index_entry:
        return {
            "ok": True,
            "address": address,
            "resolved": False,
            "entity_id": None,
            "attribution": build_attribution_block({}),
            "unknown_remains_unknown": True,
        }

    cluster_id = index_entry.get("cluster_id")
    cluster = (seed.get("clusters") or {}).get(cluster_id, {})
    entity = (seed.get("entities") or {}).get(cluster.get("entity_id", ""), {})

    return {
        "ok": True,
        "address": address,
        "resolved": True,
        "entity_id": cluster.get("entity_id"),
        "cluster": build_cluster_version_block(cluster),
        "attribution": build_attribution_block(entity.get("attribution") or {}),
        "linked_addresses": cluster.get("addresses") or [],
        "address_count": len(cluster.get("addresses") or []),
    }


def build_entity_profile(entity_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build entity profile with linked addresses."""
    seed = seed or _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id)
    if not entity:
        return {"ok": False, "error": "entity_not_found", "entity_id": entity_id}

    clusters = [
        build_cluster_version_block(c)
        for cid, c in (seed.get("clusters") or {}).items()
        if c.get("entity_id") == entity_id
    ]
    all_addresses = []
    for c in (seed.get("clusters") or {}).values():
        if c.get("entity_id") == entity_id:
            all_addresses.extend(c.get("addresses") or [])

    return {
        "ok": True,
        "entity_id": entity_id,
        "entity_type": entity.get("entity_type", "unknown"),
        "attribution": build_attribution_block(entity.get("attribution") or {}),
        "clusters": clusters,
        "linked_addresses": all_addresses,
        "address_count": len(all_addresses),
        "source_confidence_version_mandatory": True,
    }


def build_entity_resolution_panel(
    *,
    entity_id: str | None = None,
    address: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()

    if address:
        resolution = resolve_address(address, seed)
        result = {"resolution": resolution}
    elif entity_id:
        profile = build_entity_profile(entity_id, seed)
        if not profile.get("ok"):
            return {**profile, "feature_id": _FEATURE_ID}
        result = {"profile": profile}
    else:
        result = {
            "entity_count": len(seed.get("entities") or {}),
            "cluster_count": len(seed.get("clusters") or {}),
            "address_index_count": len(seed.get("address_index") or {}),
        }

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "priority": _PRIORITY,
        "critical_infrastructure": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "foundation_feature": True,
        "depends_on_by": ["#532", "#539", "#540", "#542", "#516"],
        **result,
        "acceptance_criteria": {
            "source_confidence_version_mandatory": True,
            "unknown_remains_unknown": True,
            "cluster_versioning": True,
            "no_ai_attribution_without_evidence": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def entity_resolution_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "priority": _PRIORITY,
        "critical_infrastructure": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "foundation_feature": True,
        "entity_count": len(seed.get("entities") or {}),
        "cluster_count": len(seed.get("clusters") or {}),
        "acceptance_criteria": {
            "source_confidence_version_mandatory": True,
            "unknown_remains_unknown": True,
            "cluster_versioning": True,
            "no_ai_attribution_without_evidence": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
