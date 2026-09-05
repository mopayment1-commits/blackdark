"""
Alpha Engine feature extraction (#13) — MVP 8-feature set.

Start small (5-10 features) before scaling to 100+.
"""

from __future__ import annotations

from typing import Any


def extract_alpha_features(ctx: dict[str, Any]) -> dict[str, float]:
    """
    Extract 8 interpretable features from gathered alpha inputs.

    Features are normalized to 0-100 scale for ensemble scoring.
    """
    price = ctx.get("sources", {}).get("coingecko") or {}
    fg = ctx.get("sources", {}).get("alternative_me_fear_greed") or {}
    entity = ctx.get("sources", {}).get("arkham_entity") or {}

    change_24h = float(price.get("change_24h_pct") or 0)
    momentum_24h = max(0.0, min(100.0, 50 + change_24h * 3))
    momentum_7d_proxy = max(0.0, min(100.0, 50 + change_24h * 1.5))
    fear_greed = float(fg.get("alpha_score") or fg.get("value") or 50)
    entity_flow = float(entity.get("alpha_score") or entity.get("entity_flow_score") or 50)
    liquidity = 75.0 if price.get("ok") and not price.get("fallback") else 40.0
    volume_ratio = max(0.0, min(100.0, 50 + abs(change_24h) * 2))
    volatility_24h = max(0.0, min(100.0, min(abs(change_24h) * 5, 100)))
    trend_strength = max(0.0, min(100.0, 50 + change_24h * 4))

    return {
        "momentum_24h": round(momentum_24h, 2),
        "momentum_7d_proxy": round(momentum_7d_proxy, 2),
        "fear_greed": round(fear_greed, 2),
        "entity_flow": round(entity_flow, 2),
        "liquidity": round(liquidity, 2),
        "volume_ratio": round(volume_ratio, 2),
        "volatility_24h": round(volatility_24h, 2),
        "trend_strength": round(trend_strength, 2),
    }


def build_explanations(features: dict[str, float], *, bias: str, score: float) -> list[dict[str, Any]]:
    """Human-readable reasons for the alpha signal."""
    reasons: list[dict[str, Any]] = []

    if features.get("momentum_24h", 50) >= 60:
        reasons.append(
            {
                "factor": "momentum_24h",
                "direction": "bullish",
                "weight": "high",
                "text": "24h price momentum is positive — trend supports upside bias.",
            }
        )
    elif features.get("momentum_24h", 50) <= 40:
        reasons.append(
            {
                "factor": "momentum_24h",
                "direction": "bearish",
                "weight": "high",
                "text": "24h price momentum is negative — short-term weakness detected.",
            }
        )

    fg = features.get("fear_greed", 50)
    if fg >= 65:
        reasons.append(
            {
                "factor": "fear_greed",
                "direction": "bearish",
                "weight": "medium",
                "text": "Elevated greed reading — contrarian caution on sentiment extremes.",
            }
        )
    elif fg <= 35:
        reasons.append(
            {
                "factor": "fear_greed",
                "direction": "bullish",
                "weight": "medium",
                "text": "Elevated fear reading — contrarian accumulation signal.",
            }
        )

    ef = features.get("entity_flow", 50)
    if ef >= 58:
        reasons.append(
            {
                "factor": "entity_flow",
                "direction": "bullish",
                "weight": "medium",
                "text": "Entity/whale flow score favors accumulation.",
            }
        )
    elif ef <= 42:
        reasons.append(
            {
                "factor": "entity_flow",
                "direction": "bearish",
                "weight": "medium",
                "text": "Entity/whale flow score favors distribution.",
            }
        )

    if features.get("liquidity", 50) < 50:
        reasons.append(
            {
                "factor": "liquidity",
                "direction": "neutral",
                "weight": "low",
                "text": "Liquidity confidence reduced — price source fallback active.",
            }
        )

    if not reasons:
        reasons.append(
            {
                "factor": "composite",
                "direction": bias,
                "weight": "medium",
                "text": f"Composite alpha score {score:.0f}/100 with mixed factor alignment.",
            }
        )
    return reasons
