"""
Canonical Intelligence Service — shared layer for #162 Unified API, #183 Public API, #179 MCP.

Read-only intelligence with source/freshness metadata and consistent null semantics.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

_FEATURE_IDS = {"unified_api": 162, "public_api": 183, "mcp": 179}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _freshness_meta(*, source: str, fetched_at: str | None, latency_ms: float | None, data_state: str) -> dict[str, Any]:
    return {
        "source": source,
        "fetched_at": fetched_at,
        "latency_ms": latency_ms,
        "data_state": data_state,
        "as_of": fetched_at or _utcnow(),
    }


def _null_safe(value: Any) -> Any:
    """Consistent null semantics — explicit None, never sentinel strings for missing numbers."""
    if value is None:
        return None
    if isinstance(value, float) and (value != value):  # NaN
        return None
    return value


async def get_price_intelligence(asset: str = "BTC") -> dict[str, Any]:
    """Canonical price response for API + MCP."""
    t0 = time.perf_counter()
    from bd_platform.price_aggregation_engine import aggregate_prices

    sym = asset.upper().replace("/USDT", "")
    row = await aggregate_prices(sym, use_cache=True)
    elapsed = time.perf_counter() - t0

    if not row.get("ok"):
        return {
            "ok": False,
            "asset": sym,
            "price_usd": None,
            "vwap_usd": None,
            "change_24h_pct": None,
            "error": row.get("error") or "price_unavailable",
            "freshness": _freshness_meta(source="price_aggregation_engine", fetched_at=None, latency_ms=None, data_state="UNAVAILABLE"),
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    meta = row.get("source_metadata") or {}
    fetched = row.get("timestamp") or _utcnow()
    return {
        "ok": True,
        "asset": sym,
        "price_usd": _null_safe(row.get("weighted_price")),
        "vwap_usd": _null_safe(row.get("vwap_usd")),
        "change_24h_pct": _null_safe(row.get("change_24h_pct")),
        "outlier_count": _null_safe(row.get("outlier_count")),
        "source_count": _null_safe(meta.get("connectors_ok")),
        "price_verified": bool((row.get("validation") or {}).get("price_verified")),
        "freshness": _freshness_meta(
            source=str(meta.get("primary_source") or "multi_connector_vwap"),
            fetched_at=fetched,
            latency_ms=_null_safe(row.get("latency_ms")),
            data_state=str(row.get("data_state") or "LIVE"),
        ),
        "citation": "GET /api/v1/blackdark/price/{asset}",
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


async def get_market_health_intelligence(asset: str = "BTC") -> dict[str, Any]:
    """Canonical market health for API + MCP."""
    t0 = time.perf_counter()
    from bd_platform.market_health_engine import build_market_health_dashboard

    sym = asset.upper().replace("/USDT", "")
    row = await build_market_health_dashboard(sym)
    elapsed = time.perf_counter() - t0

    if not row.get("ok"):
        return {
            "ok": False,
            "asset": sym,
            "overall_score": None,
            "overall_status": None,
            "error": "market_health_unavailable",
            "freshness": _freshness_meta(source="market_health_engine", fetched_at=None, latency_ms=None, data_state="UNAVAILABLE"),
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    return {
        "ok": True,
        "asset": sym,
        "overall_score": _null_safe(row.get("overall_score")),
        "overall_status": row.get("overall_status"),
        "classification_reason": row.get("classification_reason"),
        "pillar_count": _null_safe(row.get("pillar_count")),
        "pillars": row.get("pillars") or [],
        "freshness": _freshness_meta(
            source="market_health_engine",
            fetched_at=row.get("timestamp"),
            latency_ms=_null_safe(row.get("latency_ms")),
            data_state="LIVE" if not row.get("cache_hit") else "CACHED",
        ),
        "citation": "GET /api/v1/blackdark/market-health/{asset}",
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


async def get_risk_score_intelligence(asset: str = "BTC") -> dict[str, Any]:
    """Canonical risk/confidence score for API + MCP (Feature #149)."""
    t0 = time.perf_counter()
    from bd_platform.confidence_engine import score_asset_confidence

    sym = asset.upper().replace("/USDT", "")
    row = await score_asset_confidence(sym)
    elapsed = time.perf_counter() - t0

    if not row.get("ok"):
        return {
            "ok": False,
            "asset": sym,
            "risk_score": None,
            "confidence_score": None,
            "error": "risk_score_unavailable",
            "freshness": _freshness_meta(source="confidence_engine", fetched_at=None, latency_ms=None, data_state="UNAVAILABLE"),
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    confidence = _null_safe(row.get("confidence_score"))
    # Risk score = inverse of confidence for agent readability (higher = riskier)
    risk_score = round(100 - float(confidence), 1) if confidence is not None else None

    return {
        "ok": True,
        "asset": sym,
        "risk_score": risk_score,
        "confidence_score": confidence,
        "confidence_band": row.get("confidence_band"),
        "phase_label": row.get("phase_label"),
        "criteria_count": _null_safe(len(row.get("criteria") or [])),
        "freshness": _freshness_meta(
            source="confidence_engine_phase_1",
            fetched_at=row.get("timestamp"),
            latency_ms=_null_safe(row.get("latency_ms")),
            data_state="LIVE",
        ),
        "citation": "GET /api/v1/blackdark/risk-score/{asset}",
        "disclaimer": "Experimental rule-based confidence — not investment advice",
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def blackdark_api_status() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "BLACKDARK API",
        "api_version": "v1",
        "feature_ids": _FEATURE_IDS,
        "mode": "read_only",
        "endpoints": [
            "GET /api/v1/blackdark/price/{asset}",
            "GET /api/v1/blackdark/market-health/{asset}",
            "GET /api/v1/blackdark/risk-score/{asset}",
            "GET /api/v1/blackdark/status",
        ],
        "auth": "X-API-Key required (free tier rate limited)",
        "null_semantics": "Missing values returned as null — never synthetic defaults",
        "timestamp": _utcnow(),
    }
