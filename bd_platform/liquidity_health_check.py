"""
Liquidity Health Check — Feature #142 (Sprint 2).

Liquidity analysis before any token purchase decision:
  - Total liquidity
  - Liquidity concentration
  - Lock status (when metadata available)
  - Slippage estimates for $1K / $10K / $100K orders

Integrates with #193 Smart Contract Scanner (LP safety hook).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.LiquidityHealth")

_FEATURE_ID = 142
_ORDER_SIZES_USD = (1_000, 10_000, 100_000)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _estimate_slippage_bps(*, order_usd: float, liquidity_usd: float) -> float:
    """Simple square-root market impact model."""
    if liquidity_usd <= 0:
        return 999.0
    participation = order_usd / liquidity_usd
    return min(500.0, round(participation**0.5 * 10_000, 2))


def _concentration_risk(liquidity_usd: float, fdv_usd: float | None) -> dict[str, Any]:
    """Proxy concentration — high if liquidity << market cap."""
    if not fdv_usd or fdv_usd <= 0:
        return {"concentration_risk": "unknown", "ratio": None}
    ratio = liquidity_usd / fdv_usd
    if ratio < 0.01:
        return {"concentration_risk": "high", "ratio": round(ratio, 4), "detail": "Liquidity < 1% of FDV"}
    if ratio < 0.05:
        return {"concentration_risk": "medium", "ratio": round(ratio, 4)}
    return {"concentration_risk": "low", "ratio": round(ratio, 4)}


async def analyze_liquidity_health(asset: str, *, chain: str = "ethereum") -> dict[str, Any]:
    """Liquidity Health Check for a single asset."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    from bd_platform.onchain_hub import dexscreener_pairs

    dex = await dexscreener_pairs(sym)
    pairs = dex.get("pairs") or []

    if not pairs:
        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "asset": sym,
            "error": "no_liquidity_data",
            "headline": f"No liquidity data found for {sym} — do not buy without analysis",
            "sla_met": elapsed <= 2000,
            "latency_ms": round(elapsed, 1),
            "timestamp": _utcnow(),
        }

    # Best pair by liquidity
    best = max(pairs, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
    liq_usd = float((best.get("liquidity") or {}).get("usd") or 0)
    fdv = float(best.get("fdv") or best.get("marketCap") or 0) or None
    price = float(best.get("priceUsd") or 0)
    dex_id = str(best.get("dexId") or "unknown")
    pair_addr = str(best.get("pairAddress") or "")

    slippage_table = []
    for size in _ORDER_SIZES_USD:
        bps = _estimate_slippage_bps(order_usd=size, liquidity_usd=liq_usd)
        slippage_table.append({
            "order_usd": size,
            "estimated_slippage_bps": bps,
            "estimated_slippage_pct": round(bps / 100, 2),
            "safe": bps < 100,
        })

    concentration = _concentration_risk(liq_usd, fdv)
    lock_status = "unknown"
    labels = best.get("labels") or []
    if any("locked" in str(l).lower() for l in labels):
        lock_status = "locked"
    elif liq_usd > 500_000:
        lock_status = "likely_deep_pool"

    # #193 hook placeholder
    lp_safety = {
        "scanner": "#193_smart_contract_scanner",
        "lp_token_safety_check": "recommended_before_purchase",
        "pair_address": pair_addr,
    }

    health_score = 100
    if concentration["concentration_risk"] == "high":
        health_score -= 30
    if slippage_table[0]["estimated_slippage_bps"] > 50:
        health_score -= 20
    if liq_usd < 100_000:
        health_score -= 25
    health_score = max(0, health_score)

    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Liquidity Health Check",
        "asset": sym,
        "chain": chain,
        "total_liquidity_usd": round(liq_usd, 2),
        "price_usd": price,
        "dex": dex_id,
        "pair_address": pair_addr,
        "liquidity_concentration": concentration,
        "lock_status": lock_status,
        "slippage_estimates": slippage_table,
        "health_score": health_score,
        "health_label": "healthy" if health_score >= 70 else "caution" if health_score >= 40 else "risky",
        "headline": (
            f"{sym}: ${liq_usd:,.0f} liquidity on {dex_id} — "
            f"$1K slippage ~{slippage_table[0]['estimated_slippage_pct']:.1f}%"
        ),
        "lp_safety": lp_safety,
        "policy": "No purchase without Liquidity Analysis visible",
        "integrated_features": ["#193"],
        "sla_met": elapsed <= 2000,
        "latency_ms": round(elapsed, 1),
        "timestamp": _utcnow(),
    }


def liquidity_health_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "order_sizes_usd": list(_ORDER_SIZES_USD),
        "data_source": "dexscreener",
        "integrated_features": ["#193"],
        "timestamp": _utcnow(),
    }
