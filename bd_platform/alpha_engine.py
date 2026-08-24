"""
Alpha Engine (#13) — multi-source signal hub.

Aggregates data source inputs (CoinGecko, Alternative.me F&G, Arkham entity flows)
into a unified alpha score with explanations. MVP: 8 features, rule-based ensemble.
Target metrics: Sharpe ≥0.8, Max DD ≤25% (improve over time).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from bd_platform.alpha_features import build_explanations, extract_alpha_features

logger = logging.getLogger("BLACKDARK.AlphaEngine")

_FEATURE_WEIGHTS = {
    "momentum_24h": 0.20,
    "momentum_7d_proxy": 0.10,
    "fear_greed": 0.20,
    "entity_flow": 0.20,
    "liquidity": 0.15,
    "volume_ratio": 0.05,
    "volatility_24h": 0.05,
    "trend_strength": 0.05,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _composite(features: dict[str, float]) -> float:
    total = 0.0
    for key, weight in _FEATURE_WEIGHTS.items():
        total += float(features.get(key, 50)) * weight
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

    ctx = {
        "symbol": sym,
        "sources": {
            "coingecko": price,
            "alternative_me_fear_greed": fg,
            "arkham_entity": entity,
        },
        "timestamp": _utcnow(),
    }
    features = extract_alpha_features(ctx)
    ctx["features"] = features
    # Legacy factor map for backward compatibility
    ctx["factors"] = {
        "momentum": features["momentum_24h"],
        "sentiment_fg": features["fear_greed"],
        "entity_flow": features["entity_flow"],
        "liquidity": features["liquidity"],
    }
    return ctx


async def compute_alpha_signal(symbol: str = "BTC") -> dict[str, Any]:
    """Alpha Engine output for one asset — unified score with explanations."""
    t0 = time.perf_counter()
    ctx = await gather_alpha_inputs(symbol)
    features = ctx["features"]
    score = _composite(features)
    fg = ctx["sources"]["alternative_me_fear_greed"]
    entity = ctx["sources"]["arkham_entity"]

    bias = "neutral"
    if score >= 60:
        bias = "bullish"
    elif score <= 40:
        bias = "bearish"

    explanations = build_explanations(features, bias=bias, score=score)
    confidence = round(min(95.0, 50 + abs(score - 50) * 0.9), 1)

    return {
        "ok": True,
        "surface": "alpha_engine",
        "asset": ctx["symbol"],
        "alpha_score": score,
        "confidence_pct": confidence,
        "bias": bias,
        "headline": f"{ctx['symbol']} alpha {score:.0f}/100 ({bias})",
        "features": features,
        "feature_count": len(features),
        "factors": ctx["factors"],
        "weights": _FEATURE_WEIGHTS,
        "explanations": explanations,
        "model": {
            "type": "weighted_ensemble_v1",
            "next": "RandomForest/XGBoost after feature stability",
            "feature_target": "8 MVP features (scale to 100+ later)",
        },
        "inputs": {
            "fear_greed": fg.get("value"),
            "fear_greed_label": fg.get("label"),
            "entity_flow_score": entity.get("entity_flow_score"),
            "entity_source": entity.get("source"),
            "price_usd": ctx["sources"]["coingecko"].get("price_usd"),
        },
        "input_sources": ["coingecko", "alternative.me", "arkham"],
        "mvp_metrics": {
            "sharpe_target": 0.8,
            "max_drawdown_pct_target": 25,
            "win_rate_target": 0.50,
            "latency_minutes_target": 5,
        },
        "data_state": "LIVE",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 3.0,
        "timestamp": _utcnow(),
        "disclaimer": "Alpha signal from multi-source inputs — not trade advice.",
    }


async def rank_alpha_universe(*, limit: int = 25) -> dict[str, Any]:
    """Rank top assets by alpha score using CoinGecko universe + engine inputs."""
    t0 = time.perf_counter()
    from blackdark.ingestion.arkham_connector import fetch_entity_intelligence_input
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_markets

    markets = await fetch_coingecko_markets(per_page=min(limit, 50))
    fg_global = await gather_alpha_inputs("BTC")
    fg_score = float(fg_global["features"]["fear_greed"])

    rankings: list[dict[str, Any]] = []
    for row in (markets.get("markets") or [])[:limit]:
        sym = str(row.get("symbol") or "").upper()
        if not sym:
            continue
        change = float(row.get("change_24h_pct") or 0)
        entity = await fetch_entity_intelligence_input(sym)
        ctx = {
            "sources": {
                "coingecko": {"change_24h_pct": change, "ok": True},
                "alternative_me_fear_greed": {"alpha_score": fg_score},
                "arkham_entity": entity,
            }
        }
        features = extract_alpha_features(ctx)
        rankings.append(
            {
                "symbol": sym,
                "canonical_id": row.get("canonical_id"),
                "alpha_score": _composite(features),
                "features": features,
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
