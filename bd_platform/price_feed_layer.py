"""
Price Feed Layer — Feature #283 (Sprint 0 infrastructure, NOT standalone).

Real-time price streaming foundation serving all platform surfaces.
NOT a product feature — rejected as standalone dashboard.
UI surfaces: Landing Page + Market Radar (deferred frontend).
Acceptance: latency/freshness always visible.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PriceFeedLayer")

_FEATURE_ID = 283
_STANDALONE = False
_ARCHIVED_STANDALONE = True
_SPRINT = 0
_MERGED_INTO = "Sprint 0 Infrastructure / Price Feed Layer"
_SEED_PATH = Path("data/price_feed_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"
_DEFAULT_STALE_MS = 5000

_UI_SURFACES = ("Landing Page", "Market Radar")

FeedType = Literal["spot", "perp", "cross"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"venues": {}, "assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("price feed layer seed load failed: %s", exc)
        return {"venues": {}, "assets": {}}


def build_freshness_block(
    *,
    latency_ms: float,
    snapshot_age_ms: float,
    exchange_timestamp: str | None = None,
    stale_threshold_ms: float = _DEFAULT_STALE_MS,
) -> dict[str, Any]:
    """Latency/freshness — mandatory on every price output."""
    stale = snapshot_age_ms > stale_threshold_ms
    return {
        "latency_ms": round(latency_ms, 1),
        "snapshot_age_ms": round(snapshot_age_ms, 1),
        "stale_threshold_ms": stale_threshold_ms,
        "stale": stale,
        "exchange_timestamp": exchange_timestamp,
        "received_timestamp": _utcnow(),
        "freshness_visible": True,
        "latency_visible": True,
        "display": (
            f"Latency: {latency_ms:.0f}ms | Age: {snapshot_age_ms:.0f}ms | "
            f"Stale: {'YES' if stale else 'NO'}"
        ),
    }


def build_venue_quote(quote: dict[str, Any]) -> dict[str, Any]:
    """Normalized venue quote with freshness metadata."""
    bid = float(quote.get("bid", 0))
    ask = float(quote.get("ask", 0))
    mid = (bid + ask) / 2 if bid and ask else float(quote.get("price", 0))
    spread_bps = round((ask - bid) / mid * 10_000, 2) if mid and bid and ask else 0.0

    freshness = build_freshness_block(
        latency_ms=float(quote.get("latency_ms", 0)),
        snapshot_age_ms=float(quote.get("snapshot_age_ms", 0)),
        exchange_timestamp=quote.get("exchange_timestamp"),
        stale_threshold_ms=float(quote.get("stale_threshold_ms", _DEFAULT_STALE_MS)),
    )

    return {
        "venue": quote.get("venue"),
        "asset": quote.get("asset"),
        "pair": quote.get("pair"),
        "feed_type": quote.get("feed_type", "spot"),
        "bid": bid,
        "ask": ask,
        "mid": round(mid, 8),
        "spread_bps": spread_bps,
        "freshness": freshness,
        "streaming": bool(quote.get("streaming", True)),
        "display": (
            f"{quote.get('asset')} @ {quote.get('venue')}: "
            f"mid={mid:,.2f} spread={spread_bps}bps | {freshness['display']}"
        ),
    }


def build_streaming_status(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    streaming = seed.get("streaming") or {}
    return {
        "mode": streaming.get("mode", "websocket"),
        "fallback": streaming.get("fallback", "rest_poll"),
        "venues_connected": streaming.get("venues_connected", 0),
        "venues_total": streaming.get("venues_total", 0),
        "updates_per_second": streaming.get("updates_per_second", 0),
        "display": (
            f"Streaming: {streaming.get('mode', 'websocket')} | "
            f"Venues: {streaming.get('venues_connected', 0)}/{streaming.get('venues_total', 0)} | "
            f"Fallback: {streaming.get('fallback', 'rest_poll')}"
        ),
    }


def build_scope_lock() -> dict[str, Any]:
    return {
        "not_standalone_feature": True,
        "archived_ticket_283": True,
        "infrastructure_layer": True,
        "serves": ["Landing Page", "Market Radar", "Data Engine", "Intelligence Ledger"],
        "no_separate_dashboard": True,
        "live_charts_deferred": True,
        "display": (
            "Price Feed Layer = Sprint 0 foundation | "
            "NOT standalone feature | "
            "UI: Landing Page + Market Radar (no separate dashboard)"
        ),
    }


def get_live_prices(asset: str = "BTC") -> dict[str, Any]:
    """Aggregate live prices from seed + live_book_hub with freshness."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    seed_quotes = (seed.get("assets") or {}).get(sym) or []

    quotes = [build_venue_quote({**q, "asset": sym}) for q in seed_quotes]

    try:
        from live_book_hub import get_best_price, get_quote_age_ms, hub_stats

        for venue_cfg in (seed.get("venues") or {}).values():
            venue = venue_cfg.get("id")
            pair = venue_cfg.get("default_pair", f"{sym}/USDT")
            if not venue:
                continue
            live = get_best_price(venue, pair)
            if live:
                elapsed = (time.perf_counter() - t0) * 1000
                age = get_quote_age_ms(venue, pair) or 0.0
                quotes.append(build_venue_quote({
                    "venue": venue,
                    "asset": sym,
                    "pair": pair,
                    "bid": live.get("bid", 0),
                    "ask": live.get("ask", 0),
                    "latency_ms": elapsed,
                    "snapshot_age_ms": age,
                    "streaming": True,
                    "feed_type": "spot",
                }))
        hub = hub_stats()
    except ImportError:
        hub = {}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    mids = [q["mid"] for q in quotes if q.get("mid", 0) > 0]
    consensus_mid = round(sum(mids) / len(mids), 2) if mids else 0.0

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "archived_standalone_ticket": _ARCHIVED_STANDALONE,
        "infrastructure_layer": True,
        "surface": "price_feed_layer",
        "asset": sym,
        "consensus_mid": consensus_mid,
        "venue_count": len(quotes),
        "quotes": quotes,
        "streaming": build_streaming_status(seed),
        "hub_stats": hub,
        "scope_lock": build_scope_lock(),
        "freshness_on_all_quotes": all(q.get("freshness", {}).get("freshness_visible") for q in quotes),
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def price_feed_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Price Feed Layer",
        "standalone": _STANDALONE,
        "archived_standalone_ticket": _ARCHIVED_STANDALONE,
        "sprint": _SPRINT,
        "merged_into": _MERGED_INTO,
        "infrastructure_layer": True,
        "scope_lock": build_scope_lock(),
        "streaming": build_streaming_status(seed),
        "ui_surfaces": list(_UI_SURFACES),
        "acceptance_criteria": {
            "latency_visible": True,
            "freshness_visible": True,
            "no_standalone_dashboard": True,
            "serves_all_surfaces": True,
        },
        "configured_assets": list((seed.get("assets") or {}).keys()),
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
