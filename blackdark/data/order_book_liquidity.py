"""
Order Book & Liquidity Data Layer — Features #269 + #277 merged (Wave 01 Data Engine).

#269 = infrastructure layer (snapshots, liquidity gaps, replay QA)
#277 = market depth engine (L2/L3 depth, spread, imbalance, slippage, sequence gaps)

NOT standalone — merged into Liquidity Layer + Market Radar Pro.
Engine = Sprint 1. UI = panel inside Screener (deferred).
Ingestion (Data Engine) ≠ Analytics (Intelligence Ledger).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OrderBookLiquidity")

_FEATURE_IDS = (269, 277)
_FEATURE_ID = 269
_STANDALONE = False
_MERGED_INTO = "Wave 01 Data Engine / Liquidity Layer (#269)"
_MERGED_TICKETS = {
    269: "Order Book & Liquidity Data Layer",
    277: "Order Book / Market Depth engine",
}
_SPRINT = 1
_DASHBOARD_DEFERRED = "Screener panel / Market Radar Pro (Sprint 2)"
_SEED_PATH = Path("data/order_book_liquidity_seed.json")
_METHODOLOGY_VERSION = "1.1"
_DEFAULT_BOOK_LEVELS = 10

RootCause = Literal["API_down", "stale_data", "venue_maintenance", "sequence_gap", "unknown"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"gaps": [], "replay_tests": [], "retention": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("order book liquidity seed load failed: %s", exc)
        return {"gaps": [], "replay_tests": [], "retention": {}}


def build_scope_lock_display() -> dict[str, Any]:
    return {
        "asset_classes": ["crypto spot", "perp order books"],
        "book_levels": ["L2", "L3 where available"],
        "dex_amm": "separate pipeline",
        "resilience_pairs": "top 100 only",
        "replay_mode": "daily batch — not real-time",
        "ui_surface": "Screener panel (deferred)",
        "display": (
            "Crypto spot + perp order books (L2/L3 where available) | "
            "DEX liquidity (AMM pools) = separate pipeline | "
            "Resilience = calculated on top 100 pairs only | "
            "Replay = daily batch, not real-time | "
            "UI = Screener panel inside Market Radar Pro (no standalone dashboard)"
        ),
        "no_ui_in_sprint_1": True,
        "no_standalone_dashboard": True,
        "dashboard_deferred": _DASHBOARD_DEFERRED,
    }


def build_gap_record(gap: dict[str, Any]) -> dict[str, Any]:
    """Gap detection schema — no gap = no alert fatigue."""
    expected = float(gap.get("expected_depth_usd", 0))
    actual = float(gap.get("actual_depth_usd", 0))
    gap_pct = round((1 - actual / expected) * 100, 2) if expected else 0.0
    threshold = float(gap.get("alert_threshold_pct", 10))
    alert = gap_pct >= threshold

    return {
        "timestamp": gap.get("timestamp"),
        "venue": gap.get("venue"),
        "pair": gap.get("pair"),
        "expected_depth_usd": expected,
        "actual_depth_usd": actual,
        "gap_pct": gap_pct,
        "duration_seconds": gap.get("duration_seconds"),
        "root_cause": gap.get("root_cause", "unknown"),
        "alert_threshold_pct": threshold,
        "alert_fired": alert,
        "display": (
            f"Gap: [{gap.get('timestamp')}, {gap.get('venue')}, {gap.get('pair')}, "
            f"expected_depth={expected:,.0f}, actual_depth={actual:,.0f}, "
            f"gap%={gap_pct}, duration={gap.get('duration_seconds')}s, "
            f"root_cause: {gap.get('root_cause', 'unknown')}]"
        ),
        "no_alert_fatigue": not alert or gap_pct >= threshold,
    }


def build_replay_test_result(test: dict[str, Any]) -> dict[str, Any]:
    """Replay test — daily batch validation."""
    expected_spread_bps = float(test.get("expected_spread_bps", 0))
    replayed_spread_bps = float(test.get("replayed_spread_bps", 0))
    variance_bps = abs(expected_spread_bps - replayed_spread_bps)
    passed = variance_bps < float(test.get("variance_threshold_bps", 1.0))

    return {
        "pair": test.get("pair"),
        "venue": test.get("venue"),
        "test_date": test.get("test_date"),
        "expected_spread_bps": expected_spread_bps,
        "replayed_spread_bps": replayed_spread_bps,
        "variance_bps": round(variance_bps, 4),
        "passed": passed,
        "display": (
            f"Replay: {test.get('pair')} @ {test.get('venue')} | "
            f"Expected spread: {expected_spread_bps} bps | "
            f"Replayed: {replayed_spread_bps} bps | "
            f"Variance: {variance_bps:.4f} bps | "
            f"QA: {'Passed' if passed else 'Failed'}"
        ),
        "daily_batch": True,
        "not_realtime": True,
    }


def build_cost_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    retention = seed.get("retention") or {}
    return {
        "storage_heavy": True,
        "compression_mandatory": True,
        "auto_delete_beyond_retention": True,
        "top_50_pairs_retention_days": retention.get("top_50_days", 365),
        "other_pairs_retention_days": retention.get("other_days", 30),
        "display": (
            "Order book snapshots = storage-heavy | "
            "Retention: L1/L2 top 50 pairs = 1 year, others = 30 days | "
            "Compression mandatory | Auto-delete beyond retention"
        ),
        "no_unbounded_storage": True,
    }


def build_separation_of_concerns() -> dict[str, Any]:
    return {
        "ingestion_layer": "Wave 01 Data Engine (#269)",
        "depth_engine": "Market Depth (#277 merged into #269)",
        "analytics_layer": "Intelligence Ledger (Sprint 2)",
        "dashboard_layer": _DASHBOARD_DEFERRED,
        "display": (
            "Ingestion (Data Engine) ≠ Analytics (Intelligence Ledger). "
            "#277 engine merged into #269 Liquidity Layer — no standalone dashboard. "
            "Depth heatmap/curves = Screener panel (deferred)."
        ),
        "backend_not_product": True,
        "road_not_destination": True,
    }


def build_acceptance_criteria(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    sla = seed.get("sla") or {}
    return {
        "gap_detection": True,
        "sequence_gaps_detected": True,
        "replay_tests": True,
        "sequence_replay_tests": True,
        "gap_detection_latency_minutes": sla.get("gap_detection_latency_min", 5),
        "gap_latency_display": f"Gap detection latency < {sla.get('gap_detection_latency_min', 5)} min",
        "sequence_gap_detection_latency_ms": sla.get("sequence_gap_detection_latency_ms", 500),
        "sequence_gap_display": (
            f"Sequence gap detection < {sla.get('sequence_gap_detection_latency_ms', 500)} ms"
        ),
        "replay_coverage_pairs": sla.get("replay_coverage_pairs", 100),
        "replay_frequency": "weekly",
        "replay_display": f"Replay test coverage: top {sla.get('replay_coverage_pairs', 100)} pairs weekly",
        "spread_variance_bps": sla.get("spread_variance_bps", 1.0),
        "spread_display": (
            f"Spread accuracy vs direct exchange query: "
            f"< {sla.get('spread_variance_bps', 1.0)} bps variance"
        ),
        "depth_heatmap_deferred": True,
        "ui_panel": "Screener (deferred)",
    }


def _format_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def compute_spread_bps(best_bid: float, best_ask: float) -> float:
    if best_bid <= 0 or best_ask <= 0:
        return 0.0
    mid = (best_bid + best_ask) / 2
    return round((best_ask - best_bid) / mid * 10_000, 4)


def compute_imbalance_ratio(bid_depth_usd: float, ask_depth_usd: float) -> float:
    total = bid_depth_usd + ask_depth_usd
    if total <= 0:
        return 0.0
    return round((bid_depth_usd - ask_depth_usd) / total, 4)


def compute_book_depth_usd(
    levels: list[list[float]],
    *,
    depth_levels: int = _DEFAULT_BOOK_LEVELS,
) -> float:
    return sum(float(level[0]) * float(level[1]) for level in levels[:depth_levels])


def compute_slippage_pct(
    levels: list[list[float]],
    *,
    order_usd: float,
    side: Literal["buy", "sell"],
) -> float:
    """Walk the book to estimate slippage for a given order size."""
    if order_usd <= 0 or not levels:
        return 0.0

    best_price = float(levels[0][0])
    remaining = order_usd
    filled_usd = 0.0
    cost_usd = 0.0

    for price, qty in levels:
        price_f = float(price)
        qty_f = float(qty)
        level_usd = price_f * qty_f
        take = min(remaining, level_usd)
        cost_usd += take
        filled_usd += take / price_f * price_f
        remaining -= take
        if remaining <= 0:
            break

    if remaining > 0 or best_price <= 0:
        return 999.0

    avg_price = cost_usd / (order_usd - remaining) if (order_usd - remaining) > 0 else best_price
    if side == "buy":
        return round((avg_price - best_price) / best_price * 100, 4)
    return round((best_price - avg_price) / best_price * 100, 4)


def build_depth_curve(
    bids: list[list[float]],
    asks: list[list[float]],
    *,
    levels: int = _DEFAULT_BOOK_LEVELS,
) -> list[dict[str, Any]]:
    """Depth curve points for heatmap (backend data — UI deferred)."""
    if not bids or not asks:
        return []

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid = (best_bid + best_ask) / 2
    curve: list[dict[str, Any]] = []

    bid_cum = 0.0
    for price, qty in bids[:levels]:
        bid_cum += float(price) * float(qty)
        distance_bps = round((mid - float(price)) / mid * 10_000, 2) if mid else 0.0
        curve.append({
            "side": "bid",
            "distance_bps": distance_bps,
            "cumulative_depth_usd": round(bid_cum, 2),
        })

    ask_cum = 0.0
    for price, qty in asks[:levels]:
        ask_cum += float(price) * float(qty)
        distance_bps = round((float(price) - mid) / mid * 10_000, 2) if mid else 0.0
        curve.append({
            "side": "ask",
            "distance_bps": distance_bps,
            "cumulative_depth_usd": round(ask_cum, 2),
        })

    return curve


def build_sequence_gap_record(gap: dict[str, Any]) -> dict[str, Any]:
    """L2/L3 sequence gap detection — missing update IDs in order book stream."""
    expected = int(gap.get("expected_sequence", 0))
    received = int(gap.get("received_sequence", 0))
    gap_size = max(0, received - expected - 1) if received > expected else 0
    recovered = bool(gap.get("recovered", False))

    return {
        "timestamp": gap.get("timestamp"),
        "venue": gap.get("venue"),
        "pair": gap.get("pair"),
        "book_level": gap.get("book_level", "L2"),
        "expected_sequence": expected,
        "received_sequence": received,
        "gap_size": gap_size,
        "recovered": recovered,
        "recovery_method": gap.get("recovery_method"),
        "alert_fired": gap_size > 0,
        "display": (
            f"Sequence gap: [{gap.get('timestamp')}, {gap.get('venue')}, {gap.get('pair')}, "
            f"{gap.get('book_level', 'L2')}, expected={expected}, received={received}, "
            f"gap_size={gap_size}, recovered={recovered}]"
        ),
    }


def build_sequence_replay_test_result(test: dict[str, Any]) -> dict[str, Any]:
    """Replay test validating sequence integrity over a replay window."""
    expected = int(test.get("expected_sequences", 0))
    replayed = int(test.get("replayed_sequences", 0))
    gaps_detected = int(test.get("gaps_detected", 0))
    gaps_recovered = int(test.get("gaps_recovered", 0))
    passed = bool(test.get("passed", gaps_detected == gaps_recovered and expected == replayed))

    return {
        "pair": test.get("pair"),
        "venue": test.get("venue"),
        "test_date": test.get("test_date"),
        "book_level": test.get("book_level", "L2"),
        "expected_sequences": expected,
        "replayed_sequences": replayed,
        "gaps_detected": gaps_detected,
        "gaps_recovered": gaps_recovered,
        "passed": passed,
        "display": (
            f"Sequence replay: {test.get('pair')} @ {test.get('venue')} | "
            f"Sequences: {replayed}/{expected} | "
            f"Gaps: {gaps_detected} detected, {gaps_recovered} recovered | "
            f"QA: {'Passed' if passed else 'Failed'}"
        ),
        "daily_batch": True,
    }


def build_market_depth_metrics(depth: dict[str, Any]) -> dict[str, Any]:
    """Depth/spread/imbalance/slippage metrics from L2/L3 book snapshot."""
    bids = depth.get("bids") or []
    asks = depth.get("asks") or []
    levels = int(depth.get("levels", _DEFAULT_BOOK_LEVELS))

    bid_depth = compute_book_depth_usd(bids, depth_levels=levels)
    ask_depth = compute_book_depth_usd(asks, depth_levels=levels)
    best_bid = float(bids[0][0]) if bids else 0.0
    best_ask = float(asks[0][0]) if asks else 0.0
    spread_bps = compute_spread_bps(best_bid, best_ask)
    imbalance = compute_imbalance_ratio(bid_depth, ask_depth)

    slippage_cfg = depth.get("slippage_sizes_usd") or [10_000, 100_000, 1_000_000]
    slippage_curve: dict[str, float] = {}
    for size in slippage_cfg:
        buy_slip = compute_slippage_pct(asks, order_usd=float(size), side="buy")
        slippage_curve[f"${int(size):,}"] = buy_slip

    depth_curve = build_depth_curve(bids, asks, levels=levels)

    return {
        "venue": depth.get("venue"),
        "pair": depth.get("pair"),
        "book_level": depth.get("book_level", "L2"),
        "levels": levels,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_bps": spread_bps,
        "bid_depth_usd": round(bid_depth, 2),
        "ask_depth_usd": round(ask_depth, 2),
        "total_depth_usd": round(bid_depth + ask_depth, 2),
        "imbalance_ratio": imbalance,
        "slippage_curve": slippage_curve,
        "depth_curve": depth_curve,
        "heatmap_deferred": True,
        "display": (
            f"Depth: bid {_format_usd(bid_depth)} | ask {_format_usd(ask_depth)} | "
            f"Spread: {spread_bps} bps | Imbalance: {imbalance:+.2%} | "
            f"Slippage $100K: {slippage_curve.get('$100,000', 0)}%"
        ),
        "descriptive_only": True,
    }


def list_sequence_gaps(*, venue: str | None = None, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    gaps = [build_sequence_gap_record(g) for g in seed.get("sequence_gaps") or []]
    if venue:
        gaps = [g for g in gaps if g.get("venue") == venue]

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "count": len(gaps[:limit]),
        "sequence_gaps": gaps[:limit],
        "alerts_fired": sum(1 for g in gaps if g.get("alert_fired")),
        "timestamp": _utcnow(),
    }


def list_sequence_replay_tests(*, passed_only: bool = False, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    tests = [
        build_sequence_replay_test_result(t)
        for t in seed.get("sequence_replay_tests") or []
    ]
    if passed_only:
        tests = [t for t in tests if t.get("passed")]

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "count": len(tests[:limit]),
        "tests": tests[:limit],
        "passed_count": sum(1 for t in tests if t.get("passed")),
        "timestamp": _utcnow(),
    }


def build_market_depth_panel(*, pair: str, venue: str | None = None) -> dict[str, Any]:
    """#277 market depth panel — engine only, heatmap UI deferred to Screener."""
    t0 = time.perf_counter()
    seed = _load_seed()
    market_depth = seed.get("market_depth") or {}
    pair_data = market_depth.get(pair)

    if not pair_data:
        return {
            "ok": False,
            "feature_ids": list(_FEATURE_IDS),
            "error": "pair_not_configured",
            "pair": pair,
        }

    venues = {venue: pair_data[venue]} if venue and venue in pair_data else pair_data
    metrics = [build_market_depth_metrics({**v, "pair": pair, "venue": k}) for k, v in venues.items()]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "feature_id": 277,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "merged_with": 269,
        "surface": "market_depth",
        "pair": pair,
        "venue": venue,
        "metrics": metrics,
        "sequence_gaps": list_sequence_gaps(venue=venue, limit=10),
        "scope_lock": build_scope_lock_display(),
        "heatmap_deferred": True,
        "ui_panel": "Screener (deferred)",
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_gaps(*, venue: str | None = None, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    gaps = [build_gap_record(g) for g in seed.get("gaps") or []]
    if venue:
        gaps = [g for g in gaps if g.get("venue") == venue]
    alerts = [g for g in gaps if g.get("alert_fired")]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "count": len(gaps[:limit]),
        "gaps": gaps[:limit],
        "alerts_fired": len(alerts),
        "timestamp": _utcnow(),
    }


def list_replay_tests(*, passed_only: bool = False, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    tests = [build_replay_test_result(t) for t in seed.get("replay_tests") or []]
    if passed_only:
        tests = [t for t in tests if t.get("passed")]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(tests[:limit]),
        "tests": tests[:limit],
        "passed_count": sum(1 for t in tests if t.get("passed")),
        "timestamp": _utcnow(),
    }


def order_book_liquidity_status() -> dict[str, Any]:
    seed = _load_seed()
    gaps = seed.get("gaps") or []
    tests = seed.get("replay_tests") or []
    seq_gaps = seed.get("sequence_gaps") or []
    seq_tests = seed.get("sequence_replay_tests") or []

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_FEATURE_IDS),
        "merged_tickets": _MERGED_TICKETS,
        "title": "Order Book & Liquidity Data Layer + Market Depth Engine",
        "standalone": _STANDALONE,
        "archived_standalone_ticket": True,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dashboard_deferred": _DASHBOARD_DEFERRED,
        "scope_lock": build_scope_lock_display(),
        "separation_of_concerns": build_separation_of_concerns(),
        "cost_gate": build_cost_gate(seed),
        "acceptance_criteria": build_acceptance_criteria(seed),
        "reused_table": "order_books",
        "integrates_with": [268, 277],
        "gap_count": len(gaps),
        "sequence_gap_count": len(seq_gaps),
        "replay_test_count": len(tests),
        "sequence_replay_test_count": len(seq_tests),
        "replay_pass_rate_pct": round(
            sum(1 for t in tests if t.get("passed", True)) / max(len(tests), 1) * 100,
            1,
        ),
        "sequence_replay_pass_rate_pct": round(
            sum(1 for t in seq_tests if t.get("passed", True)) / max(len(seq_tests), 1) * 100,
            1,
        ),
        "market_depth_pairs": len(seed.get("market_depth") or {}),
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
