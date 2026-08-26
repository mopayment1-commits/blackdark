"""
Whale Flow Destination Tracker — Feature #510 (Sprint 1 On-Chain Intelligence Layer).

Renamed from "Whale Wallet Inflow Wallet Destination AI Profiling".
Integrated into Whale Intelligence Module — rule-based destination tagging, no AI.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.WhaleFlowDestinationTracker")

_FEATURE_ID = 510
_RENAMED_FROM = "Whale Wallet Inflow Wallet Destination AI Profiling"
_TITLE = "Whale Flow Destination Tracker"
_STANDALONE = False
_MERGED_INTO = "On-Chain Intelligence Layer / Whale Intelligence Module"
_LAYER = "On-Chain Intelligence Layer"
_SPRINT = 1
_SEED_PATH = Path("data/whale_flow_destination_tracker_seed.json")
_METHODOLOGY_VERSION = "1.0"

DestinationType = Literal["exchange", "cold_wallet", "defi", "unknown"]

_DISCLAIMER = (
    "On-chain tracking only | Not AI prediction | Not portfolio management | "
    "Destination tagging = heuristic-based (known exchange addresses, contract identification)"
)

_BANNED_TERMS = (
    "ai profiling",
    "ai prediction",
    "portfolio management",
    "will sell",
    "will buy",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"flows": [], "destination_rules": {}, "known_addresses": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("whale flow destination tracker seed load failed: %s", exc)
        return {"flows": [], "destination_rules": {}, "known_addresses": {}}


def build_destination_heuristics(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    rules = seed.get("destination_rules") or {}
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "method": "rule_based_heuristics",
        "no_ai": True,
        "no_ml": True,
        "rules": rules.get("rules") or [
            "known_exchange_address_match",
            "contract_type_identification",
            "cold_wallet_pattern_detection",
            "defi_protocol_address_match",
        ],
        "confidence_basis": "heuristic_based",
        "not_ai_prediction": True,
        "display": "Rule-based destination tagging — exchange/cold/DeFi/unknown",
    }


def tag_destination(
    address: str,
    *,
    known_addresses: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based destination tagging — no AI."""
    known = known_addresses or {}
    entry = known.get(address.lower(), {})

    if entry:
        dest_type: DestinationType = entry.get("type", "unknown")
        label = entry.get("label", "Unknown")
        confidence = entry.get("confidence", "heuristic_high")
    else:
        dest_type = "unknown"
        label = "Unknown"
        confidence = "heuristic_low"

    return {
        "address": address,
        "destination_type": dest_type,
        "destination_label": label,
        "confidence": confidence,
        "confidence_basis": "heuristic_based",
        "not_ai_prediction": True,
        "rule_based": True,
        "display": f"Destination: {label} ({dest_type}) | Confidence: heuristic-based",
    }


def build_whale_flow_record(flow: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Format whale flow tracking record."""
    seed = seed or _load_seed()
    known = seed.get("known_addresses") or {}
    amount_usd = float(flow.get("amount_usd", 0))
    dest_address = flow.get("destination_address", "")
    dest = tag_destination(dest_address, known_addresses=known)

    return {
        "whale_address": flow.get("whale_address"),
        "asset": flow.get("asset", "BTC"),
        "amount_usd": amount_usd,
        "destination": dest,
        "chain": flow.get("chain", "ethereum"),
        "tx_hash": flow.get("tx_hash"),
        "tracking_only": True,
        "not_portfolio_management": True,
        "not_ai_prediction": True,
        "display": (
            f"Whale moved ${amount_usd:,.0f} to [{dest['destination_label']}] | "
            f"Confidence: heuristic-based"
        ),
        "timestamp": flow.get("timestamp") or _utcnow(),
    }


def build_whale_flow_destination_panel(
    *,
    asset: str | None = None,
    whale_address: str | None = None,
) -> dict[str, Any]:
    """Main panel — whale flow destination tracking feed."""
    t0 = time.perf_counter()
    seed = _load_seed()
    flows_raw = seed.get("flows") or []

    if asset:
        flows_raw = [f for f in flows_raw if f.get("asset", "").upper() == asset.upper()]
    if whale_address:
        flows_raw = [
            f for f in flows_raw
            if f.get("whale_address", "").lower() == whale_address.lower()
        ]

    flows = [build_whale_flow_record(f, seed) for f in flows_raw]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "no_ai_profiling": True,
        "tracking_only": True,
        "not_portfolio_management": True,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "surface": "onchain_intelligence_feed",
        "rule_based_only": True,
        "flows": flows,
        "flow_count": len(flows),
        "heuristics": build_destination_heuristics(seed),
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def whale_flow_destination_tracker_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "no_ai_profiling": True,
        "tracking_only": True,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "rule_based_only": True,
        "heuristics": build_destination_heuristics(seed),
        "flow_record_count": len(seed.get("flows") or []),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
