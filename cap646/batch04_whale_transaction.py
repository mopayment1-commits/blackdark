"""Capability #183 — Whale Transaction Intelligence.

DISTINCT from Batch03 #130 (transaction_risk_insight / swap slippage+gas):
#183 focuses on large-transfer whale classification, flow direction, and
concentration risk — not DEX swap execution simulation.
"""

from __future__ import annotations

from typing import Any

WHALE_THRESHOLD_USD = 100_000.0
MEGA_WHALE_THRESHOLD_USD = 1_000_000.0
SHARK_THRESHOLD_USD = 10_000.0


def classify_whale_tier(amount_usd: float) -> str:
    if amount_usd >= MEGA_WHALE_THRESHOLD_USD:
        return "mega_whale"
    if amount_usd >= WHALE_THRESHOLD_USD:
        return "whale"
    if amount_usd >= SHARK_THRESHOLD_USD:
        return "shark"
    return "retail"


def compute_whale_risk_score(*, amount_usd: float, tier: str, flow_direction: str) -> float:
    """Rule-based risk score 0–100 — not a learned model."""
    base = min(100.0, max(0.0, amount_usd / WHALE_THRESHOLD_USD * 10))
    tier_boost = {"mega_whale": 15.0, "whale": 8.0, "shark": 3.0, "retail": 0.0}.get(tier, 0.0)
    flow_boost = 5.0 if flow_direction in {"exchange_inflow", "exchange_outflow"} else 0.0
    return round(min(100.0, base + tier_boost + flow_boost), 1)


def build_whale_transaction_intelligence(
    *,
    symbol: str,
    address: str,
    amount_usd: float,
    flow_direction: str = "unknown",
    block_timestamp: str | None = None,
) -> dict[str, Any]:
    tier = classify_whale_tier(amount_usd)
    risk_score = compute_whale_risk_score(amount_usd=amount_usd, tier=tier, flow_direction=flow_direction)
    is_whale_event = tier in {"whale", "mega_whale"}

    return {
        "ok": True,
        "feature_ref": 183,
        "symbol": symbol.upper(),
        "address": address,
        "catalog_goal": "whale_transaction_intelligence",
        "amount_usd": amount_usd,
        "whale_tier": tier,
        "flow_direction": flow_direction,
        "risk_score": risk_score,
        "is_whale_event": is_whale_event,
        "concentration_signal": is_whale_event and flow_direction == "exchange_inflow",
        "distinct_from_130": {
            "canonical_130_scope": "swap_slippage_gas_contract_risk",
            "scope_183": "large_transfer_whale_classification",
            "reused_link": False,
        },
        "block_timestamp": block_timestamp,
        "rule_based": True,
        "ai_classification": "rule-based",
        "insight_not_recommendation": True,
    }
