#!/usr/bin/env python3
"""
G3 — 24h Reliability Soak Test (Feature #1 / #2).

Prerequisite: G2 PASS.

Usage:
  python scripts/g3_reliability_soak_test.py --hours 24
  python scripts/g3_reliability_soak_test.py --hours 1   # smoke / CI

Outputs:
  HOURLY_OPERATION_REPORTS/hourly_<timestamp>.json
  HOURLY_OPERATION_REPORTS/trend_<timestamp>.json
  FEATURE_001_G3_SOAK_TEST_REPORT.md

Trend milestones (vs Hour 1 baseline): 1, 6, 12, 18, 24

Assessment sections:
  - Environment baseline
  - Performance trend
  - Reliability trend
  - Data integrity trend
  - Recovery trend
  - Final PASS/FAIL (after 24h via --finalize)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORT_PATH = ROOT / "FEATURE_001_G3_SOAK_TEST_REPORT.md"
HOURLY_DIR = ROOT / "HOURLY_OPERATION_REPORTS"
TREND_MILESTONE_HOURS = (1, 6, 12, 18, 24)  # 1-based hour labels for trend comparison

logger = logging.getLogger("BLACKDARK.G3Soak")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _configure_env() -> None:
    os.environ.setdefault("EXCHANGE_WS_ENABLED", "true")
    os.environ.setdefault("HFT_ENGINE_ENABLED", "false")
    os.environ.setdefault("KAFKA_PRICE_STREAM_ENABLED", "false")
    os.environ.setdefault("PRICE_FEED_WS_ONLY", "true")
    os.environ.setdefault("REDIS_REQUIRED", "false")
    os.environ.setdefault("ULTRA_WS_KRAKEN_REST_DISABLED", "true")
    os.environ.setdefault("WS_STALE_HEARTBEAT_MS", "3000")
    os.environ.setdefault("WS_FAILOVER_WARMUP_SEC", "30")
    os.environ.setdefault("ARB_TIME_SYNC_WINDOW_MS", "2000")
    if not os.getenv("REDIS_URL"):
        os.environ["REDIS_PRICE_CACHE_ENABLED"] = "false"


def _process_memory_mb() -> float | None:
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        return None


def _process_cpu_percent() -> float | None:
    try:
        import psutil

        return round(psutil.Process().cpu_percent(interval=0.5), 2)
    except Exception:
        return None


def _pct_change(baseline: float | None, current: float | None) -> float | None:
    if baseline is None or current is None or baseline == 0:
        return None
    return round((current - baseline) / baseline * 100.0, 2)


def _degradation_pct(baseline: float | None, current: float | None) -> float | None:
    """Positive % means performance got worse (throughput dropped or latency rose)."""
    if baseline is None or current is None or baseline == 0:
        return None
    return round((baseline - current) / baseline * 100.0, 2)


def _latency_drift_pct(baseline: float | None, current: float | None) -> float | None:
    if baseline is None or current is None or baseline == 0:
        return None
    return round((current - baseline) / baseline * 100.0, 2)


def _apply_hourly_deltas(snapshot: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    if not previous:
        snapshot["hourly_deltas"] = {
            "ticks_processed": snapshot.get("ticks_processed"),
            "ticks_enqueued": snapshot.get("ticks_enqueued"),
            "tick_processing_rate_per_sec": None,
            "reconnect_count": 0,
            "stale_reconnects": 0,
            "frozen_events": 0,
            "failover_activations": 0,
            "gap_alerts": 0,
            "sequence_violations": 0,
            "recovery_actions": 0,
            "rejected_ticks": 0,
            "duplicates_prevented": 0,
            "disconnect_count": 0,
            "data_recovery_completeness_pct": None,
        }
        snapshot["data_integrity_rates"] = _integrity_hourly_rates(snapshot, snapshot["hourly_deltas"])
        return snapshot

    def _delta(key: str) -> int | None:
        cur = snapshot.get(key)
        prev = previous.get(key)
        if cur is None or prev is None:
            return None
        return int(cur) - int(prev)

    processed_delta = _delta("ticks_processed")
    rate = round(processed_delta / 3600.0, 2) if processed_delta is not None else None
    gap_delta = _delta("gap_alerts")
    recovery_delta = _delta("recovery_actions_total")
    recovery_pct = None
    if gap_delta is not None and gap_delta > 0 and recovery_delta is not None:
        recovery_pct = round(min(100.0, recovery_delta / gap_delta * 100.0), 2)

    snapshot["hourly_deltas"] = {
        "ticks_processed": processed_delta,
        "ticks_enqueued": _delta("ticks_enqueued"),
        "tick_processing_rate_per_sec": rate,
        "reconnect_count": _delta("reconnect_count"),
        "stale_reconnects": _delta("stale_reconnects"),
        "frozen_events": _delta("frozen_events"),
        "failover_activations": _delta("failover_activations"),
        "gap_alerts": gap_delta,
        "sequence_violations": _delta("sequence_violations"),
        "recovery_actions": recovery_delta,
        "rejected_ticks": _delta("rejected_ticks_total"),
        "duplicates_prevented": _delta("duplicates_prevented_total"),
        "disconnect_count": (
            (_delta("total_reconnects") or 0) + (_delta("stale_reconnects") or 0)
            if _delta("total_reconnects") is not None
            else None
        ),
        "data_recovery_completeness_pct": recovery_pct,
        "memory_mb_delta": (
            round(float(snapshot["memory_mb"]) - float(previous["memory_mb"]), 2)
            if snapshot.get("memory_mb") is not None and previous.get("memory_mb") is not None
            else None
        ),
    }
    snapshot["data_integrity_rates"] = _integrity_hourly_rates(snapshot, snapshot["hourly_deltas"])
    return snapshot


def _ws_stability_score(snapshot: dict[str, Any]) -> dict[str, Any]:
    streams_total = int(snapshot.get("streams_total") or 0)
    streams_connected = int(snapshot.get("streams_connected") or 0)
    deltas = snapshot.get("hourly_deltas") or {}
    reconnects = int(deltas.get("reconnect_count") or 0)
    stale = int(deltas.get("stale_reconnects") or 0)
    frozen = int(deltas.get("frozen_events") or 0)
    connected_ratio = round(streams_connected / streams_total, 3) if streams_total else None
    # Lower instability score is better (fewer reconnects/frozen per hour).
    instability = reconnects + stale + frozen
    return {
        "streams_connected_ratio": connected_ratio,
        "hourly_reconnects": reconnects,
        "hourly_stale_reconnects": stale,
        "hourly_frozen_events": frozen,
        "instability_events": instability,
    }


def compute_trend_analysis(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare milestone hours (1,6,12,18,24) against Hour 1 baseline."""
    if not hourly:
        return {"available": False, "reason": "no hourly snapshots"}

    baseline = hourly[0]
    baseline_hour = 1
    baseline_rate = (baseline.get("hourly_deltas") or {}).get("tick_processing_rate_per_sec")
    baseline_mem = baseline.get("memory_mb")
    baseline_queue = baseline.get("queue_hwm")
    baseline_latency = baseline.get("latency_p95_ms")
    baseline_ws = _ws_stability_score(baseline)

    comparisons: list[dict[str, Any]] = []
    alerts: list[str] = []

    for label in TREND_MILESTONE_HOURS:
        idx = label - 1
        row: dict[str, Any] = {"hour_label": label, "hour_index": idx, "available": False}
        if idx >= len(hourly):
            row["reason"] = "not reached yet"
            comparisons.append(row)
            continue

        snap = hourly[idx]
        ws = _ws_stability_score(snap)
        rate = (snap.get("hourly_deltas") or {}).get("tick_processing_rate_per_sec")

        mem_growth = _pct_change(baseline_mem, snap.get("memory_mb"))
        latency_drift = _latency_drift_pct(baseline_latency, snap.get("latency_p95_ms"))
        queue_growth = _pct_change(baseline_queue, snap.get("queue_hwm"))
        tick_degradation = _degradation_pct(baseline_rate, rate)

        row.update(
            {
                "available": True,
                "timestamp": snap.get("timestamp"),
                "memory_mb": snap.get("memory_mb"),
                "memory_growth_pct": mem_growth,
                "latency_p95_ms": snap.get("latency_p95_ms"),
                "latency_drift_pct": latency_drift,
                "queue_hwm": snap.get("queue_hwm"),
                "queue_growth_pct": queue_growth,
                "tick_processing_rate_per_sec": rate,
                "tick_processing_degradation_pct": tick_degradation,
                "ws_stability": {
                    "baseline_instability": baseline_ws.get("instability_events"),
                    "current_instability": ws.get("instability_events"),
                    "instability_change": (
                        int(ws.get("instability_events") or 0) - int(baseline_ws.get("instability_events") or 0)
                    ),
                    "streams_connected_ratio": ws.get("streams_connected_ratio"),
                    "hourly_reconnects": ws.get("hourly_reconnects"),
                    "hourly_stale_reconnects": ws.get("hourly_stale_reconnects"),
                    "hourly_frozen_events": ws.get("hourly_frozen_events"),
                },
            }
        )

        if mem_growth is not None and mem_growth > 25:
            alerts.append(f"Hour {label}: memory growth {mem_growth}% exceeds 25% threshold")
        if latency_drift is not None and latency_drift > 50:
            alerts.append(f"Hour {label}: latency drift {latency_drift}% exceeds 50% threshold")
        if queue_growth is not None and queue_growth > 100:
            alerts.append(f"Hour {label}: queue HWM growth {queue_growth}% exceeds 100% threshold")
        if tick_degradation is not None and tick_degradation > 20:
            alerts.append(f"Hour {label}: tick processing degradation {tick_degradation}% exceeds 20% threshold")
        if ws.get("instability_events", 0) > baseline_ws.get("instability_events", 0) * 2 + 5:
            alerts.append(f"Hour {label}: WS instability rising (reconnects/frozen events)")

        comparisons.append(row)

    return {
        "available": True,
        "baseline_hour": baseline_hour,
        "baseline_timestamp": baseline.get("timestamp"),
        "milestone_hours": list(TREND_MILESTONE_HOURS),
        "comparisons": comparisons,
        "alerts": alerts,
        "trend_verdict": "WARN" if alerts else "OK",
    }


def _write_trend_artifacts(run_id: str, hourly: list[dict[str, Any]], trend: dict[str, Any]) -> Path:
    path = HOURLY_DIR / f"trend_{run_id}.json"
    path.write_text(json.dumps(trend, indent=2, default=str), encoding="utf-8")
    return path


def _safe_rate_pct(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(float(numerator) / float(denominator) * 100.0, 4)


def collect_environment_baseline() -> dict[str, Any]:
    import config

    cpu_count = os.cpu_count()
    mem_total_mb = None
    try:
        import psutil

        mem_total_mb = round(psutil.virtual_memory().total / (1024 * 1024), 2)
    except Exception:
        pass

    return {
        "captured_at": _utcnow(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": sys.version.split()[0],
        "python_full": sys.version,
        "cpu_count": cpu_count,
        "memory_total_mb": mem_total_mb,
        "workspace": str(ROOT),
        "env": {
            "EXCHANGE_WS_ENABLED": os.getenv("EXCHANGE_WS_ENABLED", "true"),
            "HFT_ENGINE_ENABLED": os.getenv("HFT_ENGINE_ENABLED", "false"),
            "PRICE_FEED_WS_ONLY": os.getenv("PRICE_FEED_WS_ONLY", "true"),
            "REDIS_URL": bool(os.getenv("REDIS_URL")),
            "REDIS_PRICE_CACHE_ENABLED": os.getenv("REDIS_PRICE_CACHE_ENABLED", "false"),
            "WS_STALE_HEARTBEAT_MS": os.getenv("WS_STALE_HEARTBEAT_MS", "3000"),
            "WS_FAILOVER_WARMUP_SEC": os.getenv("WS_FAILOVER_WARMUP_SEC", "30"),
            "ARB_TIME_SYNC_WINDOW_MS": os.getenv("ARB_TIME_SYNC_WINDOW_MS", "2000"),
            "WS_HUB_SYMBOL_LIMIT": getattr(config, "WS_HUB_SYMBOL_LIMIT", 105),
        },
        "venues": sorted(
            config.live_price_venues() if hasattr(config, "live_price_venues") else config.WS_PRICE_VENUES
        ),
        "symbol_limit": int(getattr(config, "WS_HUB_SYMBOL_LIMIT", 105)),
    }


def _exchange_divergence_bps() -> float | None:
    from live_book_hub import get_best_price

    mids: list[float] = []
    for venue in ("binance", "okx", "bybit"):
        row = get_best_price(venue, "BTC/USDT", require_fresh=False)
        if row and row.get("mid"):
            mids.append(float(row["mid"]))
    if len(mids) < 2:
        return None
    ref = sum(mids) / len(mids)
    if ref <= 0:
        return None
    return round((max(mids) - min(mids)) / ref * 10_000, 2)


async def _collect_data_integrity_snapshot() -> dict[str, Any]:
    from feed_lag_scanner import missing_data_stats
    from live_book_hub import hub_stats
    from price_sanitize_layer import sanitize_stats

    gaps = missing_data_stats()
    sanitize = sanitize_stats()
    book = hub_stats()
    rejected = sanitize.get("rejected") or {}
    rejected_total = sum(int(v) for v in rejected.values())

    duplicates_prevented = 0
    try:
        from redis_price_cache import cache_stats

        duplicates_prevented = int(cache_stats().get("duplicates_prevented") or 0)
    except Exception:
        pass

    symbol_count = int(book.get("symbol_count") or 0)
    stale_quotes = int(book.get("stale_quotes") or 0)
    divergence_bps = _exchange_divergence_bps()

    return {
        "gap_alerts_total": int(gaps.get("gap_alerts_sent") or 0),
        "sequence_violations_total": int(gaps.get("sequence_violations_total") or 0),
        "recovery_actions_total": int(gaps.get("recovery_actions") or 0),
        "rejected_ticks_total": rejected_total,
        "rejected_breakdown": rejected,
        "duplicates_prevented_total": duplicates_prevented,
        "stale_quotes": stale_quotes,
        "symbol_count": symbol_count,
        "exchange_divergence_bps": divergence_bps,
    }


def _collect_recovery_snapshot(streams: list[dict[str, Any]], resilience: dict[str, Any]) -> dict[str, Any]:
    disconnected = sum(1 for s in streams if not s.get("connected"))
    return {
        "total_reconnects": int(resilience.get("total_reconnects") or 0),
        "stale_reconnects": int(resilience.get("stale_reconnects") or 0),
        "disconnect_count_cumulative": int(resilience.get("total_reconnects") or 0)
        + int(resilience.get("stale_reconnects") or 0),
        "avg_reconnect_time_ms": resilience.get("avg_reconnect_time_ms"),
        "max_reconnect_time_ms": resilience.get("max_reconnect_time_ms"),
        "reconnect_delay_samples": int(resilience.get("reconnect_delay_samples") or 0),
        "streams_disconnected": disconnected,
        "streams_connected": sum(1 for s in streams if s.get("connected")),
        "streams_total": len(streams),
        "failed_reconnect_attempts": disconnected,
    }


def _integrity_hourly_rates(snapshot: dict[str, Any], deltas: dict[str, Any]) -> dict[str, Any]:
    enq = deltas.get("ticks_enqueued") or snapshot.get("ticks_enqueued")
    processed = deltas.get("ticks_processed") or snapshot.get("ticks_processed")
    base = processed or enq

    sym_count = int(snapshot.get("symbol_count") or snapshot.get("book_symbol_count") or 0)
    stale = int(snapshot.get("stale_quotes") or 0)

    return {
        "missing_ticks_pct": _safe_rate_pct(deltas.get("gap_alerts"), base),
        "duplicate_ticks_pct": _safe_rate_pct(deltas.get("duplicates_prevented"), base),
        "out_of_order_ticks_pct": _safe_rate_pct(deltas.get("sequence_violations"), base),
        "rejected_ticks_pct": _safe_rate_pct(deltas.get("rejected_ticks"), base),
        "stale_data_pct": round(stale / sym_count * 100.0, 4) if sym_count > 0 else None,
        "exchange_divergence_bps": snapshot.get("exchange_divergence_bps"),
        "exchange_divergence_pct": (
            round(float(snapshot["exchange_divergence_bps"]) / 100.0, 4)
            if snapshot.get("exchange_divergence_bps") is not None
            else None
        ),
    }


def _milestone_rows(hourly: list[dict[str, Any]], extractor) -> list[dict[str, Any]]:
    rows = []
    for label in TREND_MILESTONE_HOURS:
        idx = label - 1
        if idx >= len(hourly):
            rows.append({"hour_label": label, "available": False})
            continue
        snap = hourly[idx]
        deltas = snap.get("hourly_deltas") or {}
        rows.append({"hour_label": label, "available": True, "timestamp": snap.get("timestamp"), **extractor(snap, deltas)})
    return rows


def compute_data_integrity_trend(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    if not hourly:
        return {"available": False}

    def _extract(snap: dict[str, Any], deltas: dict[str, Any]) -> dict[str, Any]:
        rates = snap.get("data_integrity_rates") or _integrity_hourly_rates(snap, deltas)
        return {"rates": rates, **rates}

    milestones = _milestone_rows(hourly, _extract)
    baseline = milestones[0].get("rates") if milestones and milestones[0].get("available") else {}
    alerts: list[str] = []
    for row in milestones:
        if not row.get("available") or row.get("hour_label") == 1:
            continue
        rates = row.get("rates") or {}
        if rates.get("missing_ticks_pct") is not None and rates["missing_ticks_pct"] > 5.0:
            alerts.append(f"Hour {row['hour_label']}: missing ticks {rates['missing_ticks_pct']}% > 5%")
        if rates.get("rejected_ticks_pct") is not None and rates["rejected_ticks_pct"] > 2.0:
            alerts.append(f"Hour {row['hour_label']}: rejected ticks {rates['rejected_ticks_pct']}% > 2%")
        if rates.get("stale_data_pct") is not None and rates["stale_data_pct"] > 10.0:
            alerts.append(f"Hour {row['hour_label']}: stale data {rates['stale_data_pct']}% > 10%")
        if rates.get("exchange_divergence_bps") is not None and rates["exchange_divergence_bps"] > 50:
            alerts.append(f"Hour {row['hour_label']}: exchange divergence {rates['exchange_divergence_bps']} bps > 50")

    return {
        "available": True,
        "baseline_hour": 1,
        "baseline_rates": baseline,
        "milestones": milestones,
        "alerts": alerts,
        "verdict": "WARN" if alerts else "OK",
    }


def compute_recovery_trend(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    if not hourly:
        return {"available": False}

    def _extract(snap: dict[str, Any], deltas: dict[str, Any]) -> dict[str, Any]:
        recovery = snap.get("recovery") or {}
        return {
            "disconnect_count": deltas.get("disconnect_count"),
            "avg_reconnect_time_ms": recovery.get("avg_reconnect_time_ms"),
            "max_reconnect_time_ms": recovery.get("max_reconnect_time_ms"),
            "failed_reconnect_attempts": recovery.get("failed_reconnect_attempts"),
            "data_recovery_completeness_pct": deltas.get("data_recovery_completeness_pct"),
            "recovery_actions": deltas.get("recovery_actions"),
            "gap_alerts": deltas.get("gap_alerts"),
        }

    milestones = _milestone_rows(hourly, _extract)
    alerts: list[str] = []
    for row in milestones:
        if not row.get("available"):
            continue
        if row.get("avg_reconnect_time_ms") is not None and row["avg_reconnect_time_ms"] > 5000:
            alerts.append(f"Hour {row['hour_label']}: avg reconnect {row['avg_reconnect_time_ms']}ms > 5000ms")
        completeness = row.get("data_recovery_completeness_pct")
        if completeness is not None and completeness < 80.0:
            alerts.append(f"Hour {row['hour_label']}: recovery completeness {completeness}% < 80%")

    return {
        "available": True,
        "milestones": milestones,
        "alerts": alerts,
        "verdict": "WARN" if alerts else "OK",
    }


def compute_reliability_trend(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    if not hourly:
        return {"available": False}

    perf = compute_trend_analysis(hourly)
    def _extract(snap: dict[str, Any], deltas: dict[str, Any]) -> dict[str, Any]:
        ws = _ws_stability_score(snap)
        return {
            "streams_connected_ratio": ws.get("streams_connected_ratio"),
            "instability_events": ws.get("instability_events"),
            "failover_activations": deltas.get("failover_activations"),
            "uptime_streams_connected": snap.get("streams_connected"),
            "uptime_streams_total": snap.get("streams_total"),
        }

    milestones = _milestone_rows(hourly, _extract)
    return {
        "available": True,
        "milestones": milestones,
        "ws_performance_comparisons": perf.get("comparisons", []),
        "alerts": perf.get("alerts", []),
        "verdict": perf.get("trend_verdict", "OK"),
    }


def compute_performance_trend(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    trend = compute_trend_analysis(hourly)
    trend["section"] = "performance"
    return trend


def compute_full_g3_assessment(
    hourly: list[dict[str, Any]],
    *,
    environment_baseline: dict[str, Any] | None,
    hours_required: int = 24,
    fatal_error: str | None = None,
) -> dict[str, Any]:
    performance = compute_performance_trend(hourly)
    reliability = compute_reliability_trend(hourly)
    integrity = compute_data_integrity_trend(hourly)
    recovery = compute_recovery_trend(hourly)

    all_alerts = (
        (performance.get("alerts") or [])
        + (reliability.get("alerts") or [])
        + (integrity.get("alerts") or [])
        + (recovery.get("alerts") or [])
    )

    hours_completed = len(hourly)
    complete = hours_completed >= hours_required and not fatal_error

    fail_reasons: list[str] = []
    if fatal_error:
        fail_reasons.append(f"fatal_error: {fatal_error}")
    if hours_completed < hours_required:
        fail_reasons.append(f"incomplete: {hours_completed}/{hours_required} hours")
    if complete and performance.get("trend_verdict") == "WARN":
        fail_reasons.append("performance trend WARN")
    if complete and integrity.get("verdict") == "WARN":
        fail_reasons.append("data integrity trend WARN")
    if complete and recovery.get("verdict") == "WARN":
        fail_reasons.append("recovery trend WARN")

    g3_verdict = "IN_PROGRESS"
    if complete:
        g3_verdict = "PASS" if not fail_reasons else "FAIL"

    return {
        "environment_baseline": environment_baseline,
        "performance_trend": performance,
        "reliability_trend": reliability,
        "data_integrity_trend": integrity,
        "recovery_trend": recovery,
        "hours_completed": hours_completed,
        "hours_required": hours_required,
        "all_alerts": all_alerts,
        "fail_reasons": fail_reasons,
        "g3_verdict": g3_verdict,
    }


def _write_baseline_artifact(run_id: str, baseline: dict[str, Any]) -> Path:
    path = HOURLY_DIR / f"baseline_{run_id}.json"
    path.write_text(json.dumps(baseline, indent=2, default=str), encoding="utf-8")
    return path


def _write_assessment_artifact(run_id: str, assessment: dict[str, Any]) -> Path:
    path = HOURLY_DIR / f"assessment_{run_id}.json"
    path.write_text(json.dumps(assessment, indent=2, default=str), encoding="utf-8")
    return path


async def _collect_hourly_snapshot(hour_index: int, elapsed_sec: float) -> dict[str, Any]:
    from exchange_ws_hub import ws_hub_stats
    from feed_lag_scanner import missing_data_stats
    from live_book_hub import get_best_price, hub_stats
    from ultra_tick_ingress import ingress_stats
    from ws_stream_resilience import all_stream_health, resilience_stats

    latencies: list[float] = []
    for venue in ("binance", "okx", "bybit"):
        row = get_best_price(venue, "BTC/USDT", require_fresh=False)
        if row and row.get("age_ms") is not None:
            latencies.append(float(row["age_ms"]))

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else None
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 2 else p50
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) >= 2 else p95

    hub = ws_hub_stats()
    ingress = ingress_stats()
    book = hub_stats()
    resilience = resilience_stats()
    streams = all_stream_health()
    gaps = missing_data_stats()
    integrity = await _collect_data_integrity_snapshot()
    recovery = _collect_recovery_snapshot(streams, resilience)
    divergence_bps = integrity.get("exchange_divergence_bps")

    return {
        "hour_index": hour_index,
        "elapsed_sec": round(elapsed_sec, 1),
        "timestamp": _utcnow(),
        "cpu_percent": _process_cpu_percent(),
        "memory_mb": _process_memory_mb(),
        "queue_depth": ingress.get("queue_size"),
        "queue_hwm": ingress.get("queue_high_water_mark"),
        "ticks_enqueued": ingress.get("ticks_enqueued"),
        "ticks_processed": ingress.get("ticks_processed"),
        "ticks_coalesced": ingress.get("ticks_coalesced"),
        "ticks_priority_bypass": ingress.get("ticks_priority_bypass"),
        "backpressure_events": ingress.get("backpressure_events"),
        "book_updates_total": book.get("updates_total"),
        "book_symbol_count": book.get("symbol_count"),
        "symbol_count": book.get("symbol_count"),
        "stale_quotes": book.get("stale_quotes"),
        "failover_activations": hub.get("failover_activations"),
        "rest_fallback_ticks": hub.get("rest_fallback_ticks"),
        "reconnect_count": sum(s.get("reconnect_count", 0) for s in streams),
        "total_reconnects": resilience.get("total_reconnects"),
        "stale_reconnects": resilience.get("stale_reconnects"),
        "frozen_events": sum(s.get("frozen_events", 0) for s in streams),
        "gap_alerts": gaps.get("gap_alerts_sent"),
        "sequence_violations": gaps.get("sequence_violations_total"),
        "recovery_actions_total": gaps.get("recovery_actions"),
        "rejected_ticks_total": integrity.get("rejected_ticks_total"),
        "duplicates_prevented_total": integrity.get("duplicates_prevented_total"),
        "exchange_divergence_bps": divergence_bps,
        "data_integrity": integrity,
        "recovery": recovery,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_p99_ms": p99,
        "streams_connected": sum(1 for s in streams if s.get("connected")),
        "streams_total": len(streams),
        "ingress_avg_latency_ms": ingress.get("avg_latency_ms"),
        "api_health": {"feed_streams_connected": sum(1 for s in streams if s.get("connected"))},
    }


async def run_soak(*, hours: float) -> dict[str, Any]:
    _configure_env()
    HOURLY_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    duration_sec = max(3600.0, hours * 3600.0)
    hourly_reports: list[dict[str, Any]] = []

    log: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _utcnow(),
        "planned_hours": hours,
        "planned_duration_sec": duration_sec,
        "g2_prerequisite": "PASS required",
        "hourly_reports": [],
    }

    environment_baseline = collect_environment_baseline()
    log["environment_baseline"] = environment_baseline
    log["baseline_report_path"] = str(_write_baseline_artifact(run_id, environment_baseline))

    pipeline_started = False
    try:
        from exchange_ws_hub import start_exchange_ws_hub, stop_exchange_ws_hub
        from ultra_tick_ingress import start_ultra_tick_ingress, stop_ultra_tick_ingress

        await start_ultra_tick_ingress()
        await start_exchange_ws_hub()
        pipeline_started = True

        t_start = time.monotonic()
        hour_index = 0
        next_hour_at = t_start + 3600.0
        prev_snapshot: dict[str, Any] | None = None

        while time.monotonic() - t_start < duration_sec:
            await asyncio.sleep(30.0)
            now = time.monotonic()
            if now >= next_hour_at:
                snapshot = await _collect_hourly_snapshot(hour_index, now - t_start)
                _apply_hourly_deltas(snapshot, prev_snapshot)
                prev_snapshot = snapshot
                hourly_reports.append(snapshot)
                path = HOURLY_DIR / f"hourly_{run_id}_h{hour_index:02d}.json"
                path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
                log["hourly_reports"].append(str(path))

                trend = compute_trend_analysis(hourly_reports)
                log["trend_analysis"] = trend
                if (hour_index + 1) in TREND_MILESTONE_HOURS or hour_index + 1 == int(hours):
                    partial = compute_full_g3_assessment(
                        hourly_reports,
                        environment_baseline=log.get("environment_baseline"),
                        hours_required=int(hours),
                    )
                    partial["g3_verdict"] = "IN_PROGRESS"
                    log["assessment"] = partial
                    trend_path = _write_trend_artifacts(run_id, hourly_reports, partial["performance_trend"])
                    log["trend_report_path"] = str(trend_path)
                    log["assessment_report_path"] = str(_write_assessment_artifact(run_id, partial))
                    _write_report(log, hourly_reports, partial)

                logger.info(
                    "Hour %d snapshot | mem=%sMB queue=%s reconnects=%s trend=%s alerts=%d",
                    hour_index,
                    snapshot.get("memory_mb"),
                    snapshot.get("queue_depth"),
                    snapshot.get("stale_reconnects"),
                    trend.get("trend_verdict"),
                    len(trend.get("alerts") or []),
                )
                hour_index += 1
                next_hour_at = t_start + hour_index * 3600.0

    except Exception as exc:
        logger.exception("G3 soak failed")
        log["fatal_error"] = str(exc)
    finally:
        if pipeline_started:
            from exchange_ws_hub import stop_exchange_ws_hub
            from ultra_tick_ingress import stop_ultra_tick_ingress

            await stop_exchange_ws_hub()
            await stop_ultra_tick_ingress()
        log["finished_at"] = _utcnow()
        log["elapsed_sec"] = round(time.monotonic() - t_start, 1) if pipeline_started else 0

    completed_hours = len(hourly_reports)
    assessment = compute_full_g3_assessment(
        hourly_reports,
        environment_baseline=log.get("environment_baseline"),
        hours_required=int(hours),
        fatal_error=log.get("fatal_error"),
    )
    log["assessment"] = assessment
    log["trend_analysis"] = assessment["performance_trend"]
    if hourly_reports:
        log["trend_report_path"] = str(_write_trend_artifacts(run_id, hourly_reports, assessment["performance_trend"]))
        log["assessment_report_path"] = str(_write_assessment_artifact(run_id, assessment))

    log["summary"] = {
        "hours_completed": completed_hours,
        "hours_required": int(hours),
        "trend_verdict": assessment["performance_trend"].get("trend_verdict"),
        "integrity_verdict": assessment["data_integrity_trend"].get("verdict"),
        "recovery_verdict": assessment["recovery_trend"].get("verdict"),
        "trend_alerts": len(assessment.get("all_alerts") or []),
        "g3_verdict": assessment["g3_verdict"],
        "fail_reasons": assessment.get("fail_reasons"),
    }
    _write_report(log, hourly_reports, assessment)
    meta_path = ROOT / "data" / "g3_soak_logs" / f"g3_run_{run_id}.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    return log


def _write_report(
    log: dict[str, Any],
    hourly: list[dict[str, Any]],
    assessment: dict[str, Any] | None = None,
) -> None:
    summary = log.get("summary") or {}
    if assessment is None:
        assessment = log.get("assessment") or compute_full_g3_assessment(
            hourly,
            environment_baseline=log.get("environment_baseline"),
            hours_required=int(log.get("planned_hours") or 24),
            fatal_error=log.get("fatal_error"),
        )

    perf = assessment.get("performance_trend") or {}
    reliability = assessment.get("reliability_trend") or {}
    integrity = assessment.get("data_integrity_trend") or {}
    recovery = assessment.get("recovery_trend") or {}
    baseline = assessment.get("environment_baseline") or log.get("environment_baseline")

    lines = [
        "# Feature #001 / #002 — G3 Reliability Soak Test Report",
        "",
        f"**Run ID:** {log.get('run_id')}",
        f"**Started:** {log.get('started_at')}",
        f"**Finished:** {log.get('finished_at', 'IN PROGRESS')}",
        f"**Planned duration:** {log.get('planned_hours')} hours",
        "",
        "> Feature #1 and #2 remain **NOT COMPLETE** until G3 + all Quality Gates pass.",
        "",
    ]

    if baseline:
        lines.extend(["## Environment Baseline", ""])
        if log.get("baseline_report_path"):
            lines.append(f"**Baseline JSON:** `{log['baseline_report_path']}`")
        lines.append("```json")
        lines.append(json.dumps(baseline, indent=2)[:3500])
        lines.append("```")

    lines.extend(["", "## Hourly Reports", ""])
    for path in log.get("hourly_reports", []):
        lines.append(f"- `{path}`")
    if log.get("assessment_report_path"):
        lines.append(f"- **Full assessment:** `{log['assessment_report_path']}`")

    lines.extend(["", "## 1. Performance Trend (Hour 1 baseline)", ""])
    if perf.get("available"):
        lines.append(f"**Verdict:** `{perf.get('trend_verdict', 'N/A')}`")
        lines.extend(
            [
                "",
                "| Hour | Mem Δ% | Latency drift% | Queue Δ% | Tick deg% | WS instability Δ | Connected |",
                "|------|--------|----------------|----------|-----------|-------------------|-----------|",
            ]
        )
        for row in perf.get("comparisons", []):
            if not row.get("available"):
                lines.append(f"| {row.get('hour_label')} | — | — | — | — | — | — |")
                continue
            ws = row.get("ws_stability") or {}
            lines.append(
                f"| {row.get('hour_label')} "
                f"| {row.get('memory_growth_pct', '—')} "
                f"| {row.get('latency_drift_pct', '—')} "
                f"| {row.get('queue_growth_pct', '—')} "
                f"| {row.get('tick_processing_degradation_pct', '—')} "
                f"| {ws.get('instability_change', '—')} "
                f"| {ws.get('streams_connected_ratio', '—')} |"
            )
    else:
        lines.append("*Waiting for hourly snapshots.*")

    lines.extend(["", "## 2. Reliability Trend", ""])
    lines.append(f"**Verdict:** `{reliability.get('verdict', 'N/A')}`")
    if reliability.get("milestones"):
        lines.extend(
            [
                "",
                "| Hour | Connected ratio | Instability/hr | Failover Δ |",
                "|------|-----------------|----------------|------------|",
            ]
        )
        for row in reliability["milestones"]:
            if not row.get("available"):
                lines.append(f"| {row.get('hour_label')} | — | — | — |")
                continue
            lines.append(
                f"| {row.get('hour_label')} "
                f"| {row.get('streams_connected_ratio', '—')} "
                f"| {row.get('instability_events', '—')} "
                f"| {row.get('failover_activations', '—')} |"
            )

    lines.extend(["", "## 3. Data Integrity Trend", ""])
    lines.append(f"**Verdict:** `{integrity.get('verdict', 'N/A')}`")
    if integrity.get("milestones"):
        lines.extend(
            [
                "",
                "| Hour | Missing% | Duplicate% | OOO% | Rejected% | Stale% | Divergence bps |",
                "|------|----------|------------|------|-----------|--------|----------------|",
            ]
        )
        for row in integrity["milestones"]:
            if not row.get("available"):
                lines.append(f"| {row.get('hour_label')} | — | — | — | — | — | — |")
                continue
            rates = row.get("rates") or row
            lines.append(
                f"| {row.get('hour_label')} "
                f"| {rates.get('missing_ticks_pct', '—')} "
                f"| {rates.get('duplicate_ticks_pct', '—')} "
                f"| {rates.get('out_of_order_ticks_pct', '—')} "
                f"| {rates.get('rejected_ticks_pct', '—')} "
                f"| {rates.get('stale_data_pct', '—')} "
                f"| {rates.get('exchange_divergence_bps', '—')} |"
            )

    lines.extend(["", "## 4. Recovery Trend", ""])
    lines.append(f"**Verdict:** `{recovery.get('verdict', 'N/A')}`")
    if recovery.get("milestones"):
        lines.extend(
            [
                "",
                "| Hour | Disconnects | Avg reconnect ms | Max reconnect ms | Failed | Recovery % |",
                "|------|-------------|------------------|------------------|--------|------------|",
            ]
        )
        for row in recovery["milestones"]:
            if not row.get("available"):
                lines.append(f"| {row.get('hour_label')} | — | — | — | — | — |")
                continue
            lines.append(
                f"| {row.get('hour_label')} "
                f"| {row.get('disconnect_count', '—')} "
                f"| {row.get('avg_reconnect_time_ms', '—')} "
                f"| {row.get('max_reconnect_time_ms', '—')} "
                f"| {row.get('failed_reconnect_attempts', '—')} "
                f"| {row.get('data_recovery_completeness_pct', '—')} |"
            )

    all_alerts = assessment.get("all_alerts") or []
    if all_alerts:
        lines.extend(["", "## Alerts", ""])
        for alert in all_alerts:
            lines.append(f"- ⚠️ {alert}")

    verdict = summary.get("g3_verdict", assessment.get("g3_verdict", "IN_PROGRESS"))
    lines.extend(["", "## G3 Final Decision", ""])
    if verdict == "PASS":
        lines.append("## ✅ G3: PASS")
    elif verdict == "IN_PROGRESS":
        lines.append("## ⏳ G3: IN PROGRESS")
        lines.append(
            f"\nCompleted **{summary.get('hours_completed', len(hourly))}**/"
            f"**{summary.get('hours_required', 24)}** hourly snapshots."
        )
        lines.append("\nRun after 24h:")
        lines.append("```bash")
        lines.append("python scripts/g3_reliability_soak_test.py --finalize")
        lines.append("```")
    else:
        lines.append("## 🔴 G3: FAIL")
        for reason in assessment.get("fail_reasons") or []:
            lines.append(f"- {reason}")
        if log.get("fatal_error"):
            lines.append(f"- Fatal: `{log['fatal_error']}`")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _enrich_legacy_snapshot(snap: dict[str, Any]) -> None:
    snap.setdefault("recovery_actions_total", snap.get("recovery_actions", 0))
    snap.setdefault("rejected_ticks_total", 0)
    snap.setdefault("duplicates_prevented_total", 0)
    snap.setdefault("total_reconnects", snap.get("reconnect_count", 0))
    snap.setdefault("symbol_count", snap.get("book_symbol_count", 0))
    if "recovery" not in snap:
        snap["recovery"] = {
            "avg_reconnect_time_ms": None,
            "max_reconnect_time_ms": None,
            "failed_reconnect_attempts": max(
                0, int(snap.get("streams_total") or 0) - int(snap.get("streams_connected") or 0)
            ),
        }


def finalize_g3_run(run_id: str | None = None, *, hours_required: int = 24) -> dict[str, Any]:
    """Post-soak final report from hourly snapshots (does not stop running soak)."""
    files = sorted(HOURLY_DIR.glob("hourly_*_h*.json"))
    if run_id:
        files = [f for f in files if f.name.startswith(f"hourly_{run_id}_")]
    if not files:
        return {"available": False, "reason": "no hourly files found"}

    hourly: list[dict[str, Any]] = []
    for path in files:
        hourly.append(json.loads(path.read_text(encoding="utf-8")))

    for snap in hourly:
        _enrich_legacy_snapshot(snap)
    for i, snap in enumerate(hourly):
        if "hourly_deltas" not in snap or "data_integrity_rates" not in snap:
            _apply_hourly_deltas(snap, hourly[i - 1] if i else None)

    inferred_run_id = run_id or files[0].name.split("_h")[0].replace("hourly_", "")
    baseline_path = HOURLY_DIR / f"baseline_{inferred_run_id}.json"
    environment_baseline = None
    if baseline_path.exists():
        environment_baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    else:
        environment_baseline = collect_environment_baseline()
        environment_baseline["note"] = "Inferred post-hoc — soak started before baseline capture"

    meta_path = ROOT / "data" / "g3_soak_logs" / f"g3_run_{inferred_run_id}.json"
    fatal_error = None
    started_at = hourly[0].get("timestamp") if hourly else None
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        fatal_error = meta.get("fatal_error")
        started_at = meta.get("started_at") or started_at
        if meta.get("environment_baseline"):
            environment_baseline = meta["environment_baseline"]

    assessment = compute_full_g3_assessment(
        hourly,
        environment_baseline=environment_baseline,
        hours_required=hours_required,
        fatal_error=fatal_error,
    )

    log = {
        "run_id": inferred_run_id,
        "started_at": started_at,
        "finished_at": _utcnow(),
        "planned_hours": hours_required,
        "hourly_reports": [str(f) for f in files],
        "environment_baseline": environment_baseline,
        "baseline_report_path": str(baseline_path) if baseline_path.exists() else None,
        "assessment": assessment,
        "assessment_report_path": str(_write_assessment_artifact(inferred_run_id, assessment)),
        "trend_report_path": str(_write_trend_artifacts(inferred_run_id, hourly, assessment["performance_trend"])),
        "summary": {
            "hours_completed": len(hourly),
            "hours_required": hours_required,
            "g3_verdict": assessment["g3_verdict"],
            "fail_reasons": assessment.get("fail_reasons"),
            "trend_verdict": assessment["performance_trend"].get("trend_verdict"),
            "integrity_verdict": assessment["data_integrity_trend"].get("verdict"),
            "recovery_verdict": assessment["recovery_trend"].get("verdict"),
            "trend_alerts": len(assessment.get("all_alerts") or []),
        },
    }
    _write_report(log, hourly, assessment)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    return log


def analyze_existing_hourlies(run_id: str | None = None) -> dict[str, Any]:
    """Rebuild trend/assessment from HOURLY_OPERATION_REPORTS (for in-flight soak runs)."""
    return finalize_g3_run(run_id, hours_required=24)


def main() -> None:
    parser = argparse.ArgumentParser(description="G3 reliability soak test")
    parser.add_argument("--hours", type=float, default=24.0, help="Soak duration in hours (min 1)")
    parser.add_argument(
        "--analyze-trend",
        action="store_true",
        help="Rebuild assessment from existing HOURLY_OPERATION_REPORTS (no new soak)",
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Issue final G3 report after 24h soak (reads hourly snapshots only)",
    )
    parser.add_argument("--run-id", type=str, default=None, help="Run ID filter")
    parser.add_argument("--hours-required", type=int, default=24, help="Required hours for PASS")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.analyze_trend or args.finalize:
        result = finalize_g3_run(args.run_id, hours_required=args.hours_required)
        print(json.dumps(result.get("summary", {}), indent=2))
        print(f"Report: {REPORT_PATH}")
        return

    result = asyncio.run(run_soak(hours=max(1.0, args.hours)))
    print(json.dumps(result.get("summary", {}), indent=2))
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
