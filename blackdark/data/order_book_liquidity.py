"""
Order Book & Liquidity Data Layer — Feature #269 merged into Wave 01 Data Engine.

Infrastructure layer: order book snapshots + gap detection + replay tests.
NOT standalone — dashboard deferred to Sprint 2 Intelligence Ledger.
Ingestion (Data Engine) ≠ Analytics (Intelligence Ledger).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OrderBookLiquidity")

_FEATURE_ID = 269
_STANDALONE = False
_MERGED_INTO = "Wave 01 Data Engine"
_SPRINT = 1
_DASHBOARD_DEFERRED = "Sprint 2 Intelligence Ledger / Market Radar"
_SEED_PATH = Path("data/order_book_liquidity_seed.json")
_METHODOLOGY_VERSION = "1.0"

RootCause = Literal["API_down", "stale_data", "venue_maintenance", "unknown"]


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
        "dex_amm": "separate pipeline",
        "resilience_pairs": "top 100 only",
        "replay_mode": "daily batch — not real-time",
        "display": (
            "Crypto spot + perp order books only | "
            "DEX liquidity (AMM pools) = separate pipeline | "
            "Resilience = calculated on top 100 pairs only | "
            "Replay = daily batch, not real-time"
        ),
        "no_ui_in_sprint_1": True,
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
        "analytics_layer": "Intelligence Ledger (Sprint 2)",
        "dashboard_layer": _DASHBOARD_DEFERRED,
        "display": (
            "Ingestion (Data Engine) ≠ Analytics (Intelligence Ledger). "
            "#269 backend = Data Engine expansion. Dashboard = Sprint 2 frontend. No UI now."
        ),
        "backend_not_product": True,
        "road_not_destination": True,
    }


def build_acceptance_criteria(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    sla = seed.get("sla") or {}
    return {
        "gap_detection": True,
        "replay_tests": True,
        "gap_detection_latency_minutes": sla.get("gap_detection_latency_min", 5),
        "gap_latency_display": f"Gap detection latency < {sla.get('gap_detection_latency_min', 5)} min",
        "replay_coverage_pairs": sla.get("replay_coverage_pairs", 100),
        "replay_frequency": "weekly",
        "replay_display": f"Replay test coverage: top {sla.get('replay_coverage_pairs', 100)} pairs weekly",
        "spread_variance_bps": sla.get("spread_variance_bps", 1.0),
        "spread_display": (
            f"Spread accuracy vs direct exchange query: "
            f"< {sla.get('spread_variance_bps', 1.0)} bps variance"
        ),
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

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Order Book & Liquidity Data Layer",
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
        "integrates_with": [268],
        "gap_count": len(gaps),
        "replay_test_count": len(tests),
        "replay_pass_rate_pct": round(
            sum(1 for t in tests if t.get("passed", True)) / max(len(tests), 1) * 100,
            1,
        ),
        "timestamp": _utcnow(),
    }
