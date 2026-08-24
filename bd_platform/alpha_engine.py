"""
Alpha Engine (#13) — multi-source signal hub.

Aggregates data source inputs (CoinGecko, Alternative.me F&G, Arkham entity flows)
into a unified alpha score. NOT separate AI engines per API.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.AlphaEngine")

_WEIGHTS = {
    "momentum": 0.30,
    "sentiment_fg": 0.25,
    "entity_flow": 0.25,
    "liquidity": 0.20,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _composite(factors: dict[str, float]) -> float:
    total = 0.0
    for key, weight in _WEIGHTS.items():
        total += float(factors.get(key, 50)) * weight
    return round(max(0.0, min(100.0, total)), 2)


async def gather_alpha_inputs(symbol: str = "BTC") -> dict[str, Any]:
    """Collect all registered input sources for one asset."""
    from blackdark.ingestion.alternative_me_connector import fetch_fear_greed_index
    from blackdark.ingestion.arkham_connector import fetch_entity_intelligence_input
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

    sym = symbol.upper()
    price = await fetch_coingecko_price(sym)
    fg = await fetch_fear_greed_index()
    entity = await fetch_entity_intelligence_input(sym)

    change = float(price.get("change_24h_pct") or 0)
    momentum = max(0, min(100, 50 + change * 3))
    liquidity = 70.0 if price.get("ok") and not price.get("fallback") else 45.0

    return {
        "symbol": sym,
        "sources": {
            "coingecko": price,
            "alternative_me_fear_greed": fg,
            "arkham_entity": entity,
        },
        "factors": {
            "momentum": momentum,
            "sentiment_fg": float(fg.get("alpha_score") or 50),
            "entity_flow": float(entity.get("alpha_score") or 50),
            "liquidity": liquidity,
        },
        "timestamp": _utcnow(),
    }


async def compute_alpha_signal(symbol: str = "BTC") -> dict[str, Any]:
    """Alpha Engine output for one asset — unified score from all inputs."""
    t0 = time.perf_counter()
    ctx = await gather_alpha_inputs(symbol)
    factors = ctx["factors"]
    score = _composite(factors)
    fg = ctx["sources"]["alternative_me_fear_greed"]
    entity = ctx["sources"]["arkham_entity"]

    bias = "neutral"
    if score >= 60:
        bias = "bullish"
    elif score <= 40:
        bias = "bearish"

    return {
        "ok": True,
        "surface": "alpha_engine",
        "asset": ctx["symbol"],
        "alpha_score": score,
        "bias": bias,
        "headline": f"{ctx['symbol']} alpha {score:.0f}/100 ({bias})",
        "factors": factors,
        "weights": _WEIGHTS,
        "inputs": {
            "fear_greed": fg.get("value"),
            "fear_greed_label": fg.get("label"),
            "entity_flow_score": entity.get("entity_flow_score"),
            "entity_source": entity.get("source"),
            "price_usd": ctx["sources"]["coingecko"].get("price_usd"),
        },
        "input_sources": ["coingecko", "alternative.me", "arkham"],
        "data_state": "LIVE",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 3.0,
        "timestamp": _utcnow(),
        "disclaimer": "Alpha signal from multi-source inputs — not trade advice.",
    }


async def rank_alpha_universe(*, limit: int = 25) -> dict[str, Any]:
    """Rank top assets by alpha score using CoinGecko universe + engine inputs."""
    t0 = time.perf_counter()
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_markets

    markets = await fetch_coingecko_markets(per_page=min(limit, 50))
    fg_global = await gather_alpha_inputs("BTC")
    fg_score = float(fg_global["factors"]["sentiment_fg"])

    rankings: list[dict[str, Any]] = []
    for row in (markets.get("markets") or [])[:limit]:
        sym = str(row.get("symbol") or "").upper()
        if not sym:
            continue
        change = float(row.get("change_24h_pct") or 0)
        momentum = max(0, min(100, 50 + change * 3))
        entity = await fetch_entity_intelligence_input(sym)
        factors = {
            "momentum": momentum,
            "sentiment_fg": fg_score,
            "entity_flow": float(entity.get("alpha_score") or 50),
            "liquidity": 65.0,
        }
        rankings.append(
            {
                "symbol": sym,
                "canonical_id": row.get("canonical_id"),
                "alpha_score": _composite(factors),
                "factors": factors,
                "price_usd": row.get("price_usd"),
                "change_24h_pct": change,
            }
        )

    rankings.sort(key=lambda r: r["alpha_score"], reverse=True)
    for i, row in enumerate(rankings, start=1):
        row["rank"] = i

    return {
        "ok": True,
        "surface": "alpha_engine_ranking",
        "count": len(rankings),
        "rankings": rankings,
        "global_fear_greed": fg_global["sources"]["alternative_me_fear_greed"].get("value"),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 5.0,
        "timestamp": _utcnow(),
    }
