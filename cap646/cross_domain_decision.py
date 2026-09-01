"""Shared Cross-Domain Decision Intelligence payload (canonical #69 + batch02 #110)."""

from __future__ import annotations

from typing import Any


async def build_cross_domain_decision_payload(*, symbol: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    from bd_platform.institutional_delivery_intelligence_layer import cross_market_decision_intelligence_567
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

    seed = seed or {}
    multi_dim = build_multi_dim_analysis_73(asset=symbol, seed=seed)
    cross = cross_market_decision_intelligence_567(symbol=symbol)
    return {
        "multi_dimensional": multi_dim,
        "cross_market": cross,
        "composite_score": multi_dim.get("composite_score"),
    }
