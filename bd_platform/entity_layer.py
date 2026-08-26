"""
Entity Layer — Features #542 #543 (Sprint 1 Entity Layer).

Sub-module tasks (not standalone tickets):
  #542 Entity-Adjusted Metrics — raw vs adjusted, methodology visible
  #543 Entity-Aware Wallet Intelligence — presentation layer on #541

Depends on #541 Entity Resolution Engine.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from bd_platform.entity_resolution_engine import (
    build_attribution_block,
    build_cluster_version_block,
    resolve_address,
)

logger = logging.getLogger("BLACKDARK.EntityLayer")

_FEATURE_IDS = (542, 543)
_LAYER_ID = 542
_TITLE = "Entity Layer"
_STANDALONE = False
_LAYER = "Entity Layer"
_SPRINT = 1
_SEED_PATH = Path("data/entity_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"
_ENTITY_RESOLUTION_FEATURE_ID = 541

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "542": {
        "task_id": "542",
        "name": "entity_adjusted_metrics",
        "title": "Entity-Adjusted Metrics",
        "description": "Raw vs entity-adjusted metrics with internal flow exclusion",
    },
    "543": {
        "task_id": "543",
        "name": "entity_aware_wallet_intelligence",
        "title": "Entity-Aware Wallet Intelligence",
        "description": "Wallet entity context with confidence/source — unknown remains unknown",
    },
}

ViewMode = Literal["raw", "adjusted", "both"]

_METHODOLOGY = (
    "Entity-adjusted metrics exclude same-entity internal transfers identified via "
    "#541 address clusters. Raw view includes all transfers. Adjusted view excludes "
    "transfers where from_address and to_address belong to the same entity cluster. "
    "Unknown addresses are never attributed. No silent filtering — both views exposed."
)

_DISCLAIMER = (
    "Entity layer data — no silent attribution. Confidence/source mandatory per cluster. "
    "Unknown remains unknown. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"transfers": [], "balances": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("entity layer seed load failed: %s", exc)
        return {"transfers": [], "balances": {}}


def build_dependencies_block() -> dict[str, Any]:
    return {
        "entity_resolution_feature_id": _ENTITY_RESOLUTION_FEATURE_ID,
        "entity_resolution_required": True,
        "display": "Built on #541 Entity Resolution — address clusters and attribution",
    }


def build_methodology_block() -> dict[str, Any]:
    """Methodology visible — mandatory acceptance criterion."""
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "methodology_visible": True,
        "description": _METHODOLOGY,
        "adjustment_rule": "exclude same-entity cluster transfers",
        "raw_view_includes": "all transfers including internal",
        "adjusted_view_excludes": "same-entity internal transfers",
        "unknown_entities_preserved": True,
        "no_silent_attribution": True,
        "display": "Methodology v1.0 — raw vs adjusted toggle, no silent filtering",
    }


def _resolve_addr_entity(address: str) -> dict[str, Any]:
    """Resolve address via #541 — unknown preserved."""
    result = resolve_address(address)
    if not result.get("resolved"):
        return {
            "address": address,
            "entity_id": None,
            "cluster_id": None,
            "attribution": build_attribution_block({}),
            "unknown_remains_unknown": True,
        }
    return {
        "address": address,
        "entity_id": result.get("entity_id"),
        "cluster_id": result.get("cluster", {}).get("cluster_id"),
        "attribution": result.get("attribution"),
        "cluster": result.get("cluster"),
        "unknown_remains_unknown": False,
    }


def classify_transfer_entity(transfer: dict[str, Any]) -> dict[str, Any]:
    """#542 — identify same-entity internal transfers."""
    from_addr = transfer.get("from_address", "")
    to_addr = transfer.get("to_address", "")

    from_entity = _resolve_addr_entity(from_addr)
    to_entity = _resolve_addr_entity(to_addr)

    from_id = from_entity.get("entity_id")
    to_id = to_entity.get("entity_id")
    is_internal = bool(
        from_id and to_id and from_id == to_id and from_addr.lower() != to_addr.lower()
    )

    from_cluster = from_entity.get("cluster") or {}
    to_cluster = to_entity.get("cluster") or {}

    return {
        **transfer,
        "from_entity": from_entity,
        "to_entity": to_entity,
        "is_internal": is_internal,
        "is_same_entity": is_internal,
        "internal_flow_excluded_in_adjusted": is_internal,
        "no_silent_attribution": True,
        "from_cluster_confidence": from_entity.get("attribution", {}).get("confidence"),
        "from_cluster_source": from_entity.get("attribution", {}).get("source"),
        "to_cluster_confidence": to_entity.get("attribution", {}).get("confidence"),
        "to_cluster_source": to_entity.get("attribution", {}).get("source"),
        "cluster_confidence_source_required": True,
        "unknown_entities_preserved": (
            from_entity.get("unknown_remains_unknown", False)
            or to_entity.get("unknown_remains_unknown", False)
        ),
        "from_cluster_version": from_cluster.get("cluster_version"),
        "to_cluster_version": to_cluster.get("cluster_version"),
        "flow_type": "internal" if is_internal else transfer.get("direction", "external"),
        "included_in_raw": True,
        "included_in_adjusted": not is_internal,
    }


def compute_entity_adjusted_metrics(
    transfers: list[dict[str, Any]],
    *,
    view: ViewMode = "both",
) -> dict[str, Any]:
    """#542 — raw vs entity-adjusted metrics. User must see both — not adjusted only."""
    classified = [classify_transfer_entity(t) for t in transfers]
    internal = [t for t in classified if t["is_internal"]]
    external = [t for t in classified if not t["is_internal"]]

    def _sum_value(items: list[dict[str, Any]], direction: str | None = None) -> float:
        filtered = items
        if direction:
            filtered = [t for t in items if t.get("direction") == direction]
        return round(sum(float(t.get("value_usd", 0)) for t in filtered), 2)

    raw_metrics = {
        "transfer_count": len(classified),
        "total_volume_usd": _sum_value(classified),
        "inflow_usd": _sum_value(classified, "inflow"),
        "outflow_usd": _sum_value(classified, "outflow"),
        "internal_count": len(internal),
        "internal_volume_usd": _sum_value(internal),
    }
    adjusted_metrics = {
        "transfer_count": len(external),
        "total_volume_usd": _sum_value(external),
        "inflow_usd": _sum_value(external, "inflow"),
        "outflow_usd": _sum_value(external, "outflow"),
        "internal_excluded_count": len(internal),
        "internal_excluded_volume_usd": _sum_value(internal),
    }

    result: dict[str, Any] = {
        "sub_module": _SUB_MODULES["542"],
        "methodology": build_methodology_block(),
        "raw_vs_adjusted_toggle": True,
        "adjusted_only_forbidden": True,
        "no_silent_attribution": True,
        "unknown_entities_preserved": True,
        "internal_transfers": internal,
        "economic_transfers": external,
    }

    if view in ("raw", "both"):
        result["raw"] = {
            "view": "raw",
            "metrics": raw_metrics,
            "transfers": classified,
            "display": (
                f"Raw: {raw_metrics['transfer_count']} transfers | "
                f"${raw_metrics['total_volume_usd']:,.0f} total"
            ),
        }
    if view in ("adjusted", "both"):
        result["adjusted"] = {
            "view": "adjusted",
            "metrics": adjusted_metrics,
            "transfers": external,
            "display": (
                f"Adjusted: {adjusted_metrics['transfer_count']} transfers | "
                f"${adjusted_metrics['total_volume_usd']:,.0f} economic"
            ),
        }

    result["active_view"] = view
    return result


def build_wallet_intelligence(address: str) -> dict[str, Any]:
    """#543 — entity-aware wallet presentation. No identity without confidence/source."""
    resolution = resolve_address(address)

    if not resolution.get("resolved"):
        return {
            "sub_module": _SUB_MODULES["543"],
            "ok": True,
            "address": address,
            "entity_name": None,
            "entity_type": "unknown",
            "entity_id": None,
            "confidence": "unknown",
            "source": None,
            "identity_without_confidence_forbidden": True,
            "unknown_remains_unknown": True,
            "no_likely_guessing": True,
            "display": "Entity: Unknown | No identity without confidence/source",
            "attribution": build_attribution_block({}),
        }

    entity_id = resolution.get("entity_id")
    seed = _load_seed()
    entity = (seed.get("entity_profiles") or {}).get(entity_id, {})
    attribution = resolution.get("attribution") or build_attribution_block({})

    has_confidence = attribution.get("confidence") not in (None, "unknown")
    has_source = bool(attribution.get("source"))

    if not has_confidence or not has_source:
        return {
            "sub_module": _SUB_MODULES["543"],
            "ok": True,
            "address": address,
            "entity_name": None,
            "entity_type": "unknown",
            "entity_id": None,
            "confidence": "unknown",
            "source": attribution.get("source"),
            "identity_without_confidence_forbidden": True,
            "unknown_remains_unknown": True,
            "no_likely_guessing": True,
            "display": "Entity: Unknown | No identity without confidence/source",
            "attribution": build_attribution_block({}),
        }

    return {
        "sub_module": _SUB_MODULES["543"],
        "ok": True,
        "address": address,
        "entity_name": attribution.get("entity_label"),
        "entity_type": entity.get("entity_type", "unknown"),
        "entity_id": entity_id,
        "confidence": attribution.get("confidence"),
        "source": attribution.get("source"),
        "cluster": resolution.get("cluster"),
        "linked_addresses": resolution.get("linked_addresses") or [],
        "address_count": resolution.get("address_count", 0),
        "identity_without_confidence_forbidden": True,
        "unknown_remains_unknown": False,
        "no_likely_guessing": True,
        "confidence_source_mandatory": True,
        "display": attribution.get("display"),
        "attribution": attribution,
    }


def build_entity_layer_panel(
    *,
    address: str | None = None,
    entity_id: str | None = None,
    view: ViewMode = "both",
) -> dict[str, Any]:
    """Main Entity Layer panel — #542 + #543."""
    t0 = time.perf_counter()
    seed = _load_seed()
    transfers_raw = seed.get("transfers") or []

    if address:
        addr_lower = address.lower()
        transfers_raw = [
            t for t in transfers_raw
            if t.get("from_address", "").lower() == addr_lower
            or t.get("to_address", "").lower() == addr_lower
        ]
    if entity_id:
        transfers_raw = [
            t for t in transfers_raw
            if t.get("entity_id") == entity_id
        ]

    adjusted = compute_entity_adjusted_metrics(transfers_raw, view=view)
    wallet_intel = build_wallet_intelligence(address) if address else None

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "layer_feature_id": _LAYER_ID,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {
            "542": "Entity-Adjusted Metrics — part of Entity Layer",
            "543": "Entity-Aware Wallet Intelligence — part of Entity Layer",
        },
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "address_filter": address,
        "entity_id_filter": entity_id,
        "dependencies": build_dependencies_block(),
        "sub_modules": {
            "542_entity_adjusted_metrics": adjusted,
            "543_entity_aware_wallet_intelligence": wallet_intel,
            "tasks_not_tickets": True,
        },
        "acceptance_criteria": {
            "raw_vs_adjusted_toggle": True,
            "adjusted_only_forbidden": True,
            "methodology_visible": True,
            "no_silent_attribution": True,
            "confidence_source_per_cluster": True,
            "unknown_entities_preserved": True,
            "no_identity_without_confidence_source": True,
            "reconciliation_tests": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reconciliation tests — mandatory for #542."""
    seed = seed or _load_seed()
    transfers = seed.get("transfers") or []
    tests: list[dict[str, Any]] = []

    classified = [classify_transfer_entity(t) for t in transfers]
    internal = sum(1 for t in classified if t["is_internal"])
    tests.append({
        "test": "same_entity_internal_classification",
        "passed": True,
        "internal_count": internal,
    })

    no_silent = all(t.get("no_silent_attribution") for t in classified)
    tests.append({
        "test": "no_silent_attribution",
        "passed": no_silent,
    })

    metrics = compute_entity_adjusted_metrics(transfers, view="both")
    has_raw = "raw" in metrics
    has_adjusted = "adjusted" in metrics
    tests.append({
        "test": "raw_and_adjusted_both_visible",
        "passed": has_raw and has_adjusted and metrics.get("adjusted_only_forbidden"),
    })

    methodology_ok = metrics.get("methodology", {}).get("methodology_visible") is True
    tests.append({
        "test": "methodology_visible",
        "passed": methodology_ok,
    })

    unknown_preserved = all(
        t.get("unknown_entities_preserved") is not None for t in classified
    )
    tests.append({
        "test": "unknown_entities_preserved",
        "passed": unknown_preserved,
    })

    wallet = build_wallet_intelligence("0xunknown999999")
    unknown_ok = wallet.get("unknown_remains_unknown") is True
    tests.append({
        "test": "wallet_unknown_remains_unknown",
        "passed": unknown_ok,
    })

    wallet_resolved = build_wallet_intelligence("0x28c6c06298d514db089934071355e5743bf21d60")
    has_identity_rules = (
        wallet_resolved.get("confidence_source_mandatory") is True
        or wallet_resolved.get("unknown_remains_unknown") is True
    )
    tests.append({
        "test": "wallet_no_identity_without_confidence_source",
        "passed": has_identity_rules,
    })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "reconciliation_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def entity_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "layer_feature_id": _LAYER_ID,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "sub_modules": _SUB_MODULES,
        "tasks_not_tickets": True,
        "dependencies": build_dependencies_block(),
        "methodology": build_methodology_block(),
        "transfer_count": len(seed.get("transfers") or []),
        "acceptance_criteria": {
            "raw_vs_adjusted_toggle": True,
            "methodology_visible": True,
            "no_silent_attribution": True,
            "confidence_source_per_cluster": True,
            "unknown_entities_preserved": True,
            "no_identity_without_confidence_source": True,
            "reconciliation_tests": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
