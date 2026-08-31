"""
Liquidity Intelligence Engine — Feature #280 (Sprint 1 Core).

Absorbs #277 (Market Depth), #278 (Trade-correlated book analytics),
#279 (Resilience & freshness layer) into one intelligence layer.

NOT a dashboard — engine layer only.
UI = embedded in asset page + Screener filter (deferred).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from blackdark.data import order_book_liquidity as obl

logger = logging.getLogger("BLACKDARK.LiquidityIntelligence")

_FEATURE_ID = 280
_ABSORBED_IDS = (277, 278, 279, 280)
_STANDALONE = False
_MERGED_INTO = "Sprint 1 Core — Liquidity Intelligence Engine"
_SPRINT = 1
_SEED_PATH = Path("data/liquidity_intelligence_seed.json")
_METHODOLOGY_VERSION = "1.0"
_STALE_THRESHOLD_MS = 5_000

_ABSORBED_TICKETS = {
    277: "Market Depth (depth/spread/imbalance/slippage curves)",
    278: "Trade-correlated book analytics (L2/L3 + trades)",
    279: "Resilience & freshness layer",
    280: "Order Book Intelligence (umbrella layer)",
}

WarningType = Literal[
    "crossed_book",
    "stale_data",
    "sequence_gap_unrecovered",
    "depth_drop",
    "high_imbalance",
    "low_resilience",
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"pairs": {}, "warnings": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("liquidity intelligence seed load failed: %s", exc)
        return {"pairs": {}, "warnings": []}


def detect_crossed_book(
    bids: list[list[float]],
    asks: list[list[float]],
) -> dict[str, Any]:
    """Crossed-book handling — best bid >= best ask is invalid."""
    if not bids or not asks:
        return {
            "crossed": False,
            "best_bid": 0.0,
            "best_ask": 0.0,
            "crossed_bps": 0.0,
            "action": "no_data",
            "snapshot_usable": False,
        }

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    crossed = best_bid >= best_ask
    mid = (best_bid + best_ask) / 2 if not crossed else best_bid
    crossed_bps = round((best_bid - best_ask) / mid * 10_000, 2) if crossed and mid else 0.0

    if crossed:
        action = "reject_snapshot"
        usable = False
    else:
        action = "accept"
        usable = True

    return {
        "crossed": crossed,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "crossed_bps": crossed_bps,
        "action": action,
        "snapshot_usable": usable,
        "display": (
            f"Crossed book: {'YES' if crossed else 'NO'} | "
            f"bid={best_bid} ask={best_ask}"
            + (f" | crossed={crossed_bps}bps → {action}" if crossed else "")
        ),
    }


def build_freshness_block(freshness: dict[str, Any]) -> dict[str, Any]:
    """Latency/freshness visibility — always shown on intelligence output."""
    latency_ms = float(freshness.get("latency_ms", 0))
    snapshot_age_ms = float(freshness.get("snapshot_age_ms", 0))
    exchange_ts = freshness.get("exchange_timestamp")
    received_ts = freshness.get("received_timestamp", _utcnow())
    stale = snapshot_age_ms > _STALE_THRESHOLD_MS

    return {
        "latency_ms": round(latency_ms, 1),
        "snapshot_age_ms": round(snapshot_age_ms, 1),
        "stale_threshold_ms": _STALE_THRESHOLD_MS,
        "stale": stale,
        "exchange_timestamp": exchange_ts,
        "received_timestamp": received_ts,
        "freshness_visible": True,
        "latency_visible": True,
        "display": (
            f"Latency: {latency_ms:.0f}ms | Age: {snapshot_age_ms:.0f}ms | "
            f"Stale: {'YES' if stale else 'NO'} (threshold {_STALE_THRESHOLD_MS}ms)"
        ),
    }


def build_resilience_score(resilience: dict[str, Any]) -> dict[str, Any]:
    """#279 resilience — depth stability under gaps and recovery rate."""
    gap_recovery_rate = float(resilience.get("gap_recovery_rate_pct", 100))
    depth_stability = float(resilience.get("depth_stability_score", 1.0))
    uptime_pct = float(resilience.get("uptime_pct", 99.9))
    score = round((gap_recovery_rate / 100 * 0.4 + depth_stability * 0.4 + uptime_pct / 100 * 0.2) * 100, 1)

    if score >= 90:
        grade = "high"
    elif score >= 70:
        grade = "medium"
    else:
        grade = "low"

    return {
        "resilience_score": score,
        "grade": grade,
        "gap_recovery_rate_pct": gap_recovery_rate,
        "depth_stability_score": depth_stability,
        "uptime_pct": uptime_pct,
        "top_100_pairs_only": True,
        "display": (
            f"Resilience: {score}/100 ({grade}) | "
            f"Gap recovery: {gap_recovery_rate}% | "
            f"Depth stability: {depth_stability:.2f} | Uptime: {uptime_pct}%"
        ),
    }


def build_trade_correlation(trades: dict[str, Any]) -> dict[str, Any]:
    """#278 trade-correlated book analytics — flow vs book imbalance."""
    buy_vol = float(trades.get("buy_volume_usd", 0))
    sell_vol = float(trades.get("sell_volume_usd", 0))
    total = buy_vol + sell_vol
    trade_imbalance = round((buy_vol - sell_vol) / total, 4) if total else 0.0
    large_trades = int(trades.get("large_trades_count", 0))
    book_imbalance = float(trades.get("book_imbalance_at_snapshot", 0))
    aligned = (trade_imbalance > 0 and book_imbalance > 0) or (trade_imbalance < 0 and book_imbalance < 0)

    return {
        "buy_volume_usd": buy_vol,
        "sell_volume_usd": sell_vol,
        "trade_imbalance": trade_imbalance,
        "book_imbalance_at_snapshot": book_imbalance,
        "flow_book_aligned": aligned,
        "large_trades_count": large_trades,
        "window_seconds": trades.get("window_seconds", 60),
        "display": (
            f"Trade flow: buy {_fmt_usd(buy_vol)} / sell {_fmt_usd(sell_vol)} | "
            f"Imbalance: {trade_imbalance:+.2%} | "
            f"Book aligned: {'yes' if aligned else 'no'} | "
            f"Large trades: {large_trades}"
        ),
        "descriptive_only": True,
    }


def _fmt_usd(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def build_liquidity_warning(warning: dict[str, Any]) -> dict[str, Any]:
    """Liquidity warning — backend output, not standalone dashboard."""
    wtype: WarningType = warning.get("type", "depth_drop")
    severity = warning.get("severity", "medium")
    return {
        "type": wtype,
        "severity": severity,
        "pair": warning.get("pair"),
        "venue": warning.get("venue"),
        "timestamp": warning.get("timestamp"),
        "message": warning.get("message"),
        "actionable": warning.get("actionable", False),
        "display": (
            f"[{severity.upper()}] {wtype}: {warning.get('pair')} @ {warning.get('venue')} — "
            f"{warning.get('message')}"
        ),
    }


def _derive_warnings(
    pair: str,
    venue: str,
    *,
    crossed: dict[str, Any],
    freshness: dict[str, Any],
    resilience: dict[str, Any],
    depth_metrics: dict[str, Any],
    seed_warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []

    if crossed.get("crossed"):
        warnings.append(build_liquidity_warning({
            "type": "crossed_book",
            "severity": "high",
            "pair": pair,
            "venue": venue,
            "timestamp": _utcnow(),
            "message": f"Crossed book detected ({crossed['crossed_bps']}bps) — snapshot rejected",
            "actionable": True,
        }))

    if freshness.get("stale"):
        warnings.append(build_liquidity_warning({
            "type": "stale_data",
            "severity": "medium",
            "pair": pair,
            "venue": venue,
            "timestamp": _utcnow(),
            "message": f"Snapshot age {freshness['snapshot_age_ms']:.0f}ms exceeds {_STALE_THRESHOLD_MS}ms",
            "actionable": True,
        }))

    if resilience.get("grade") == "low":
        warnings.append(build_liquidity_warning({
            "type": "low_resilience",
            "severity": "medium",
            "pair": pair,
            "venue": venue,
            "timestamp": _utcnow(),
            "message": f"Resilience score {resilience['resilience_score']}/100 — gap recovery risk",
            "actionable": False,
        }))

    imb = abs(float(depth_metrics.get("imbalance_ratio", 0)))
    if imb > 0.3 and depth_metrics.get("snapshot_usable", True):
        warnings.append(build_liquidity_warning({
            "type": "high_imbalance",
            "severity": "low",
            "pair": pair,
            "venue": venue,
            "timestamp": _utcnow(),
            "message": f"Book imbalance {imb:.1%} — monitor execution risk",
            "actionable": False,
        }))

    for w in seed_warnings:
        if w.get("pair") == pair and (not venue or w.get("venue") == venue):
            warnings.append(build_liquidity_warning(w))

    return warnings


def build_intelligence_panel(*, pair: str, venue: str | None = None) -> dict[str, Any]:
    """Full Order Book Intelligence panel — layer only, UI deferred."""
    t0 = time.perf_counter()
    seed = _load_seed()
    pair_cfg = (seed.get("pairs") or {}).get(pair)

    if not pair_cfg:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "pair_not_configured",
            "pair": pair,
        }

    venues = {venue: pair_cfg[venue]} if venue and venue in pair_cfg else pair_cfg
    venue_panels: list[dict[str, Any]] = []

    for vname, vdata in venues.items():
        bids = vdata.get("bids") or []
        asks = vdata.get("asks") or []
        crossed = detect_crossed_book(bids, asks)

        depth_raw = {**vdata, "venue": vname, "pair": pair}
        depth_metrics = obl.build_market_depth_metrics(depth_raw) if crossed["snapshot_usable"] else {
            "venue": vname,
            "pair": pair,
            "snapshot_usable": False,
            "crossed_book": crossed,
            "display": crossed["display"],
        }
        if crossed["snapshot_usable"]:
            depth_metrics["snapshot_usable"] = True
            depth_metrics["crossed_book"] = crossed
        else:
            depth_metrics["crossed_book"] = crossed

        freshness = build_freshness_block(vdata.get("freshness") or {})
        resilience = build_resilience_score(vdata.get("resilience") or {})
        trade_corr = build_trade_correlation(vdata.get("trades") or {})

        seed_warnings = [w for w in (seed.get("warnings") or []) if w.get("pair") == pair]
        warnings = _derive_warnings(
            pair, vname,
            crossed=crossed,
            freshness=freshness,
            resilience=resilience,
            depth_metrics=depth_metrics,
            seed_warnings=seed_warnings,
        )

        venue_panels.append({
            "venue": vname,
            "depth": depth_metrics,
            "freshness": freshness,
            "resilience": resilience,
            "trade_correlation": trade_corr,
            "crossed_book": crossed,
            "warnings": warnings,
        })

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    all_warnings = [w for p in venue_panels for w in p["warnings"]]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "absorbed_ids": list(_ABSORBED_IDS),
        "absorbed_tickets": _ABSORBED_TICKETS,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "liquidity_intelligence_engine",
        "pair": pair,
        "venue": venue,
        "venues": venue_panels,
        "warning_count": len(all_warnings),
        "warnings": all_warnings,
        "sequence_gaps": obl.list_sequence_gaps(venue=venue, limit=5),
        "replay_tests": {
            "spread": obl.list_replay_tests(limit=3),
            "sequence": obl.list_sequence_replay_tests(limit=3),
        },
        "ui_deferred": True,
        "ui_surfaces": ["asset page embedded", "Screener filter"],
        "no_standalone_dashboard": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_liquidity_warnings(
    *,
    pair: str | None = None,
    severity: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    warnings = [build_liquidity_warning(w) for w in seed.get("warnings") or []]
    if pair:
        warnings = [w for w in warnings if w.get("pair") == pair]
    if severity:
        warnings = [w for w in warnings if w.get("severity") == severity]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(warnings[:limit]),
        "warnings": warnings[:limit],
        "timestamp": _utcnow(),
    }


def liquidity_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Liquidity Intelligence Engine",
        "absorbed_ids": list(_ABSORBED_IDS),
        "absorbed_tickets": _ABSORBED_TICKETS,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "layer_not_dashboard": True,
        "ui_deferred": True,
        "ui_surfaces": ["asset page embedded", "Screener filter"],
        "underlying_engine": "blackdark/data/order_book_liquidity.py (#269+#277)",
        "configured_pairs": len(seed.get("pairs") or {}),
        "acceptance_criteria": {
            "sequence_gap_detection": True,
            "crossed_book_handling": True,
            "latency_freshness_visible": True,
            "replay_tests": True,
            "liquidity_warnings": True,
            "resilience_scoring": True,
            "trade_correlation": True,
            "no_standalone_dashboard": True,
        },
        "timestamp": _utcnow(),
    }
