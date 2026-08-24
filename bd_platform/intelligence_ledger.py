"""
Intelligence Ledger — Sprint 2 execution intelligence hub.

Combines multi-source data (1inch, DexScreener, CEX, gas oracle, slippage optimizer)
into a single execution recommendation. 1inch is a data source, NOT a standalone feature.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

from bd_platform.oneinch_connector import fetch_oneinch_quote
from bd_platform.slippage_tolerance_optimizer import optimize_slippage_tolerance

logger = logging.getLogger("BLACKDARK.IntelligenceLedger")

_LEDGER_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 45.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _effective_cost_bps(
    *,
    venue: str,
    price: float,
    reference_price: float,
    slippage_bps: float,
    gas_bps: float | None,
) -> float:
    if reference_price <= 0 or price <= 0:
        return 9999.0
    price_penalty = abs(price - reference_price) / reference_price * 10_000
    return price_penalty + slippage_bps + (gas_bps or 0)


async def build_execution_intelligence(
    *,
    asset: str = "ETH",
    amount_usd: float = 10_000.0,
    chain: str = "ethereum",
    side: str = "buy",
    user_tolerance_bps: int | None = None,
) -> dict[str, Any]:
    """
    Sprint 2 Intelligence Ledger — best execution path from combined sources.
    """
    t0 = time.perf_counter()
    asset_u = asset.upper()
    cache_key = f"{asset_u}:{amount_usd}:{chain}:{side}"
    cached = _LEDGER_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        out = dict(cached[1])
        out["cache_hit"] = True
        return out

    slippage = await optimize_slippage_tolerance(
        asset_u, amount_usd=amount_usd, chain=chain, user_tolerance_bps=user_tolerance_bps
    )
    optimal_bps = int(slippage.get("optimal_slippage_bps") or 50)
    asymmetric = slippage.get("asymmetric_slippage") or {}
    _buy = asymmetric.get("buy_slippage_bps")
    _sell = asymmetric.get("sell_slippage_bps")
    side_slippage_bps = float(
        (_buy if side.lower() == "buy" else _sell) or optimal_bps
    )

    oneinch = await fetch_oneinch_quote(
        asset=asset_u,
        amount_usd=amount_usd,
        chain=chain,
        slippage_bps=optimal_bps,
        price_usd=slippage.get("optimization", {}).get("inputs", {}).get("price_usd"),
    )
    if not isinstance(oneinch, dict):
        oneinch = {"ok": False, "data_state": "MISSING"}

    ref_price = float(
        (oneinch.get("price_usd") if oneinch.get("ok") else 0)
        or slippage.get("optimization", {}).get("inputs", {}).get("price_usd")
        or 0
    )

    # CEX reference from slippage context
    cex_price = ref_price
    gas_bps = slippage.get("optimization", {}).get("inputs", {}).get("gas_cost_bps")

    routes: list[dict[str, Any]] = []

    if oneinch.get("ok"):
        q = oneinch.get("quote") or {}
        routes.append(
            {
                "venue": "1inch",
                "source": q.get("source", "1inch"),
                "price_usd": float(q.get("price_usd") or ref_price or 0),
                "liquidity_usd": float(q.get("liquidity_usd") or 0),
                "slippage_bps": side_slippage_bps,
                "gas_bps": gas_bps,
                "fallback": bool(q.get("fallback")),
                "effective_cost_bps": _effective_cost_bps(
                    venue="1inch",
                    price=float(q.get("price_usd") or ref_price or 0),
                    reference_price=cex_price or ref_price,
                    slippage_bps=side_slippage_bps,
                    gas_bps=gas_bps,
                ),
            }
        )

    amm_impact = float(
        slippage.get("optimization", {}).get("inputs", {}).get("amm_impact_bps_estimate") or 50
    )
    routes.append(
        {
            "venue": "amm_pool",
            "source": "dexscreener_depth",
            "price_usd": ref_price,
            "slippage_bps": amm_impact,
            "gas_bps": gas_bps,
            "effective_cost_bps": _effective_cost_bps(
                venue="amm",
                price=ref_price,
                reference_price=cex_price or ref_price,
                slippage_bps=amm_impact,
                gas_bps=gas_bps,
            ),
        }
    )

    cex_side_bps = float(
        (_buy if side.lower() == "buy" else _sell) or 8.0
    )
    routes.append(
        {
            "venue": "cex_spot",
            "source": "binance_depth",
            "price_usd": cex_price,
            "slippage_bps": cex_side_bps,
            "gas_bps": 0,
            "effective_cost_bps": cex_side_bps,
            "note": "CEX directional slippage from order-book walk",
        }
    )

    routes.sort(key=lambda r: r.get("effective_cost_bps", 9999))
    best = routes[0] if routes else None

    recommendation = (
        f"Use {best['venue']} with {optimal_bps}bps slippage tolerance"
        if best
        else "Insufficient route data"
    )
    if best and best.get("venue") == "1inch" and (oneinch.get("quote") or {}).get("fallback"):
        recommendation += " (1inch API unavailable — DexScreener pool proxy)"

    alerts = list(slippage.get("alerts") or [])
    if best and best.get("effective_cost_bps", 0) > 100:
        alerts.append(
            {
                "level": "medium",
                "code": "HIGH_EXECUTION_COST",
                "message": f"Best route still {best['effective_cost_bps']:.0f}bps effective cost",
            }
        )

    entry = {
        "ok": True,
        "success": True,
        "sprint": 2,
        "surface": "intelligence_ledger",
        "asset": asset_u,
        "amount_usd": amount_usd,
        "chain": chain,
        "side": side,
        "headline": recommendation,
        "recommended_route": best,
        "routes": routes,
        "slippage_optimization": slippage,
        "asymmetric_slippage": asymmetric,
        "oneinch_data_source": oneinch if oneinch.get("ok") else {"ok": False, "data_state": "MISSING"},
        "alerts": alerts,
        "data_sources": ["1inch", "dexscreener", "binance", "gas_oracle"],
        "data_state": "LIVE" if best else "MISSING",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 3.0,
        "timestamp": _utcnow(),
        "disclaimer": "Execution intelligence — not trade advice. Live execute requires user keys.",
    }

    _LEDGER_CACHE[cache_key] = (time.time(), entry)
    return entry


async def persist_ledger_entry(entry: dict[str, Any]) -> int | None:
    try:
        from database import insert_simulation_log

        asset = str(entry.get("asset") or "EXEC")
        return await insert_simulation_log(
            "intelligence_ledger",
            asset,
            json.dumps(entry, default=str),
            float((entry.get("recommended_route") or {}).get("effective_cost_bps") or 0),
        )
    except Exception:
        logger.exception("ledger persist failed")
        return None
