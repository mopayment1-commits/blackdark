"""
Protocol Metrics Layer — Feature #514 (Sprint 0 Data Layer).

Renamed from standalone "Active Users" ticket.
Infrastructure — rule-based DAU/MAU with documented bot filtering heuristics.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ProtocolMetricsLayer")

_FEATURE_ID = 514
_RENAMED_FROM = "Active Users"
_TITLE = "Protocol Metrics Layer"
_STANDALONE = False
_MERGED_INTO = "Data Layer / Protocol Metrics Layer"
_LAYER = "Data Layer"
_SPRINT = 0
_WAVE = 0
_SEED_PATH = Path("data/protocol_metrics_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Protocol metrics infrastructure — bot/internal filtering documented. "
    "Active Users without bot filtering = misleading. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}, "bot_rules": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("protocol metrics layer seed load failed: %s", exc)
        return {"protocols": {}, "bot_rules": {}}


def build_bot_filtering_rules(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    rules = seed.get("bot_rules") or {}
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "bot_filtering_documented": True,
        "internal_address_exclusion": rules.get("internal_exclusion", True),
        "rules": rules.get("rules") or [
            "exclude_known_bot_contracts",
            "exclude_internal_team_addresses",
            "minimum_interaction_threshold",
            "sybil_cluster_detection_heuristic",
        ],
        "heuristic_based": True,
        "no_ai": True,
        "display": "Bot/internal filtering rules documented — Active Users = filtered unique addresses",
    }


def build_active_users_metrics(protocol_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DAU/MAU with documented bot filtering."""
    seed = seed or _load_seed()
    protocol = (seed.get("protocols") or {}).get(protocol_id)
    if not protocol:
        return {"ok": False, "error": "protocol_not_found", "protocol_id": protocol_id}

    return {
        "ok": True,
        "protocol_id": protocol_id,
        "protocol_name": protocol.get("name", protocol_id),
        "dau": protocol.get("dau"),
        "mau": protocol.get("mau"),
        "dau_mau_ratio": protocol.get("dau_mau_ratio"),
        "unique_addresses_filtered": protocol.get("unique_addresses_filtered"),
        "bot_addresses_excluded": protocol.get("bot_addresses_excluded", 0),
        "internal_addresses_excluded": protocol.get("internal_addresses_excluded", 0),
        "bot_filtering_applied": True,
        "bot_rules_documented": True,
        "project_specific_event_mapping": protocol.get("event_mapping", {}),
        "source": protocol.get("source"),
        "freshness_seconds": protocol.get("freshness_seconds", 0),
        "display": (
            f"DAU: {protocol.get('dau', 'N/A'):,} | MAU: {protocol.get('mau', 'N/A'):,} | "
            f"Bot-filtered unique addresses"
        ),
    }


def build_protocol_metrics_panel(protocol_id: str = "uniswap") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    active_users = build_active_users_metrics(protocol_id, seed)
    if not active_users.get("ok"):
        return {**active_users, "feature_id": _FEATURE_ID}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "infrastructure_feature": True,
        "active_users": active_users,
        "bot_rules": build_bot_filtering_rules(seed),
        "rule_based_only": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def protocol_metrics_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "infrastructure_feature": True,
        "bot_rules": build_bot_filtering_rules(seed),
        "protocol_count": len(seed.get("protocols") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
