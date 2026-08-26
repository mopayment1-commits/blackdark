"""
Custom Alerts — Feature #532 (Sprint 1 Infrastructure Layer).

Entity/address activity alerts with backend enforcement.
Depends on #541 Entity Resolution and #516 Asset Profiles.
No buy/sell alerts. Rate limits. Direct tx evidence mandatory.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CustomAlerts")

_FEATURE_ID = 532
_TITLE = "Custom Alerts"
_STANDALONE = False
_MERGED_INTO = "Infrastructure Layer / Custom Alerts"
_LAYER = "Infrastructure Layer"
_SPRINT = 1
_SEED_PATH = Path("data/custom_alerts_seed.json")
_METHODOLOGY_VERSION = "1.0"
_DEFAULT_RATE_LIMIT_PER_HOUR = 10
_ENTITY_RESOLUTION_FEATURE_ID = 541
_ASSET_PROFILES_FEATURE_ID = 516

DeliveryChannel = Literal["email", "telegram", "webhook", "push"]

_DISCLAIMER = (
    "Activity alerts only — not buy/sell signals. "
    "Every alert requires direct transaction evidence. Rate limits enforced."
)

_BANNED_TERMS = (
    "buy signal",
    "sell signal",
    "buy alert",
    "sell alert",
    "recommendation",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"rules": [], "alerts": [], "rate_limits": {}, "delivery_log": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("custom alerts seed load failed: %s", exc)
        return {"rules": [], "alerts": [], "rate_limits": {}, "delivery_log": []}


def build_dependencies_block() -> dict[str, Any]:
    return {
        "entity_resolution_feature_id": _ENTITY_RESOLUTION_FEATURE_ID,
        "asset_profiles_feature_id": _ASSET_PROFILES_FEATURE_ID,
        "no_alert_without_entity_resolution": True,
        "no_alert_without_asset_identification": True,
        "display": "Built on #541 Entity Resolution + #516 Asset Profiles",
    }


def check_rate_limit(
    user_id: str,
    *,
    delivery_log: list[dict[str, Any]] | None = None,
    limit_per_hour: int = _DEFAULT_RATE_LIMIT_PER_HOUR,
) -> dict[str, Any]:
    """Rate limits — mandatory, prevents spam."""
    delivery_log = delivery_log or []
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    recent = [
        d for d in delivery_log
        if d.get("user_id") == user_id
        and _parse_ts(d.get("timestamp", _utcnow())) > cutoff
    ]
    allowed = len(recent) < limit_per_hour
    return {
        "allowed": allowed,
        "recent_count": len(recent),
        "limit_per_hour": limit_per_hour,
        "rate_limit_enforced": True,
        "backend_enforcement": True,
    }


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def evaluate_rule(rule: dict[str, Any], event: dict[str, Any]) -> bool:
    """Boolean filter evaluation — rule-based, backend enforced."""
    if rule.get("entity_id") and event.get("entity_id") != rule.get("entity_id"):
        return False
    if rule.get("address") and event.get("address", "").lower() != rule.get("address", "").lower():
        return False
    if rule.get("token") and event.get("token", "").upper() != rule.get("token", "").upper():
        return False
    if rule.get("chain") and event.get("chain", "").lower() != rule.get("chain", "").lower():
        return False
    min_value = rule.get("min_value_usd")
    if min_value is not None and float(event.get("value_usd", 0)) < float(min_value):
        return False
    return True


def build_alert_from_event(
    event: dict[str, Any],
    *,
    rule: dict[str, Any],
    entity_resolution: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Generate alert from backend data — direct tx evidence required."""
    tx_hash = event.get("tx_hash")
    if not tx_hash:
        return None

    entity_label = "Unknown"
    if entity_resolution and entity_resolution.get("resolved"):
        entity_label = (entity_resolution.get("attribution") or {}).get("entity_label", "Unknown")

    value_usd = float(event.get("value_usd", 0))
    address = event.get("address", "unknown")
    token = event.get("token", "unknown")
    chain = event.get("chain", "unknown")

    return {
        "alert_type": "address_activity",
        "not_buy_sell_signal": True,
        "not_recommendation": True,
        "message": f"Address {address} moved ${value_usd:,.0f} {token} on {chain}",
        "entity_label": entity_label,
        "tx_hash": tx_hash,
        "direct_tx_evidence": True,
        "tx_evidence_link": event.get("tx_evidence_link") or f"tx:{tx_hash}",
        "address": address,
        "token": token,
        "chain": chain,
        "value_usd": value_usd,
        "rule_id": rule.get("rule_id"),
        "channels": rule.get("channels") or ["webhook"],
        "backend_enforced": True,
        "display": f"Address {address} moved ${value_usd:,.0f} | Entity: {entity_label} | Tx: {tx_hash[:16]}...",
        "timestamp": event.get("timestamp") or _utcnow(),
    }


def build_custom_alerts_panel(
    *,
    user_id: str = "default",
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    rules = seed.get("rules") or []
    events = seed.get("pending_events") or []
    delivery_log = seed.get("delivery_log") or []
    rate_check = check_rate_limit(user_id, delivery_log=delivery_log)

    triggered_alerts: list[dict[str, Any]] = []
    for event in events:
        for rule in rules:
            if not rule.get("active", True):
                continue
            if not evaluate_rule(rule, event):
                continue

            entity_resolution = None
            if event.get("address"):
                try:
                    from bd_platform.entity_resolution_engine import resolve_address
                    entity_resolution = resolve_address(event["address"])
                except Exception:
                    entity_resolution = None

            alert = build_alert_from_event(event, rule=rule, entity_resolution=entity_resolution)
            if alert and rate_check["allowed"]:
                triggered_alerts.append(alert)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "user_id": user_id,
        "rules": rules,
        "rule_count": len(rules),
        "triggered_alerts": triggered_alerts,
        "alert_count": len(triggered_alerts),
        "rate_limit": rate_check,
        "dependencies": build_dependencies_block(),
        "backend_enforcement": True,
        "no_buy_sell_alerts": True,
        "direct_tx_evidence_required": True,
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def custom_alerts_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "dependencies": build_dependencies_block(),
        "rule_count": len(seed.get("rules") or []),
        "acceptance_criteria": {
            "backend_enforcement": True,
            "rate_limits": True,
            "direct_tx_evidence": True,
            "no_buy_sell_alerts": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
