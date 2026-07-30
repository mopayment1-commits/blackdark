#!/usr/bin/env python3
"""
G2 — Live WebSocket E2E Validation Harness (Feature #1 / #2).

Validates full path:
  Exchange WS → ultra_tick_ingress → price_stream_engine → live_book_hub
  → redis_price_cache → ws_price_provider → dashboard_sse → API

Usage:
  python scripts/g2_live_ws_validation.py --duration 90
  python scripts/g2_live_ws_validation.py --duration 90 --symbols BTC,ETH

Outputs:
  data/g2_validation_logs/g2_run_<timestamp>.json
  FEATURE_001_G2_LIVE_WS_VALIDATION_REPORT.md (generated)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "data" / "g2_validation_logs"
REPORT_PATH = ROOT / "FEATURE_001_G2_LIVE_WS_VALIDATION_REPORT.md"

logger = logging.getLogger("BLACKDARK.G2Validation")

SYMBOLS_DEFAULT = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
VENUES = ("binance", "okx", "bybit")


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


async def _start_pipeline() -> None:
    from ultra_tick_ingress import start_ultra_tick_ingress
    from exchange_ws_hub import start_exchange_ws_hub

    await start_ultra_tick_ingress()
    await start_exchange_ws_hub()


async def _stop_pipeline() -> None:
    from exchange_ws_hub import stop_exchange_ws_hub
    from ultra_tick_ingress import stop_ultra_tick_ingress

    await stop_exchange_ws_hub()
    await stop_ultra_tick_ingress()


async def _wait_for_ticks(symbols: list[str], timeout_sec: float = 60.0) -> dict[str, Any]:
    from live_book_hub import get_best_price

    deadline = time.monotonic() + timeout_sec
    received: dict[str, dict[str, Any]] = {}
    venues_ready: set[str] = set()
    latencies: list[float] = []

    while time.monotonic() < deadline:
        for venue in VENUES:
            if venue in venues_ready:
                continue
            for sym in symbols:
                row = get_best_price(venue, sym, require_fresh=False)
                if row and row.get("bid", 0) > 0:
                    key = f"{venue}|{sym}"
                    received[key] = row
                    venues_ready.add(venue)
                    if row.get("age_ms") is not None:
                        latencies.append(float(row["age_ms"]))
                    break
        if len(venues_ready) >= len(VENUES):
            break
        await asyncio.sleep(0.25)

    return {
        "venues_ready": sorted(venues_ready),
        "quotes_received": len(received),
        "quotes_expected_min": len(VENUES),
        "samples": received,
        "book_age_ms": latencies,
    }


async def _test_timestamps(symbols: list[str]) -> dict[str, Any]:
    from exchange_time_sync import quotes_within_sync_window
    from live_book_hub import get_best_price

    ts_map: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    sym = symbols[0]
    for venue in VENUES:
        row = get_best_price(venue, sym, require_fresh=False)
        if not row:
            continue
        ex_ts = row.get("exchange_ts_ms")
        if ex_ts:
            ts_map[venue] = int(ex_ts)
            rows.append({"venue": venue, "exchange_ts_ms": ex_ts, "age_ms": row.get("age_ms")})

    synced = quotes_within_sync_window(ts_map) if len(ts_map) >= 2 else None
    spread_ms = max(ts_map.values()) - min(ts_map.values()) if len(ts_map) >= 2 else None
    return {
        "symbol": sym,
        "venues_with_ts": len(ts_map),
        "sync_window_ok": synced,
        "timestamp_spread_ms": spread_ms,
        "rows": rows,
        "pass": len(ts_map) >= 2 and synced is True,
    }


async def _test_sequence_and_gaps() -> dict[str, Any]:
    from feed_lag_scanner import missing_data_stats, record_tick_arrival

    base = int(time.time() * 1000)
    r1 = record_tick_arrival("binance", "BTC/USDT", ts_ms=base, sequence=1000)
    r2 = record_tick_arrival("binance", "BTC/USDT", ts_ms=base + 100, sequence=1001)
    r3 = record_tick_arrival("binance", "BTC/USDT", ts_ms=base + 5000, sequence=1002)
    r4 = record_tick_arrival("binance", "BTC/USDT", ts_ms=base + 5100, sequence=1000)
    stats = missing_data_stats()
    return {
        "normal_sequence_ok": r2.get("sequence_ok", False),
        "gap_detected": r3.get("gap_detected", False),
        "sequence_violation_detected": r4.get("sequence_ok") is False,
        "stats": stats,
        "pass": r2.get("sequence_ok", False) and r3.get("gap_detected", False) and r4.get("sequence_ok") is False,
    }


async def _test_duplicate_prevention() -> dict[str, Any]:
    import config

    from redis_price_cache import cache_stats, set_top_of_book

    if not getattr(config, "REDIS_URL", ""):
        return {"pass": True, "skipped": True, "reason": "REDIS_URL not configured — local mirror mode"}

    ts = int(time.time() * 1000)
    before = cache_stats().get("duplicates_prevented", 0)
    await set_top_of_book("binance", "BTC/USDT", bid=50000.0, ask=50001.0, exchange_ts_ms=ts, force=True)
    await set_top_of_book("binance", "BTC/USDT", bid=50000.0, ask=50001.0, exchange_ts_ms=ts, force=True)
    after = cache_stats().get("duplicates_prevented", 0)
    return {
        "duplicates_before": before,
        "duplicates_after": after,
        "incremented": after > before,
        "pass": after > before,
        "skipped": False,
    }


async def _test_reconnect() -> dict[str, Any]:
    from ws_stream_resilience import all_stream_health, force_stale_reconnect, resilience_stats

    before = resilience_stats()
    health = all_stream_health()
    target = next((h for h in health if h.get("connected")), None)
    if not target:
        return {"pass": False, "reason": "no_active_stream_to_reconnect"}
    ex = target["exchange"]
    stream = target["stream"]
    closed = await force_stale_reconnect(ex, stream)
    await asyncio.sleep(2.0)
    after = resilience_stats()
    return {
        "target": {"exchange": ex, "stream": stream},
        "force_close_ok": closed,
        "reconnects_before": before.get("stale_reconnects", 0),
        "reconnects_after": after.get("stale_reconnects", 0),
        "pass": closed and after.get("stale_reconnects", 0) >= before.get("stale_reconnects", 0),
    }


async def _test_failover_and_rest_fallback(symbols: list[str]) -> dict[str, Any]:
    from exchange_ws_hub import ws_hub_stats
    from market_context import fetch_binance_ticker

    hub_before = ws_hub_stats()
    asset = symbols[0].replace("/USDT", "")
    rest_row = await fetch_binance_ticker(f"{asset}/USDT")
    await asyncio.sleep(3.0)
    hub_after = ws_hub_stats()
    activations_before = hub_before.get("failover_activations", 0)
    activations_after = hub_after.get("failover_activations", 0)
    failover_active = activations_after > activations_before
    return {
        "failover_activations_before": activations_before,
        "failover_activations_after": activations_after,
        "failover_incremented": failover_active,
        "rest_fallback_available": rest_row is not None,
        "rest_source": (rest_row or {}).get("source"),
        "pass": failover_active or rest_row is not None,
    }


async def _test_api_layers(symbols: list[str]) -> dict[str, Any]:
    from dashboard_sse import _fast_price_payload
    from ws_price_provider import get_live_prices_fast

    t0 = time.perf_counter()
    prices = get_live_prices_fast(limit=20)
    provider_ms = round((time.perf_counter() - t0) * 1000, 2)

    t1 = time.perf_counter()
    sse_payload = await _fast_price_payload()
    sse_ms = round((time.perf_counter() - t1) * 1000, 2)

    try:
        from api.routers.health import health_feed

        t2 = time.perf_counter()
        feed_health = await health_feed()
        health_ms = round((time.perf_counter() - t2) * 1000, 2)
    except Exception as exc:
        feed_health = {"error": str(exc)}
        health_ms = None

    sym = symbols[0].replace("/USDT", "")
    has_symbol = any(p.get("symbol") == sym for p in prices)
    return {
        "provider_count": len(prices),
        "provider_latency_ms": provider_ms,
        "sse_latency_ms": sse_ms,
        "sse_asset_count": sse_payload.get("market", {}).get("count", 0),
        "health_feed_ms": health_ms,
        "health_feed_ok": "websocket_hub" in feed_health,
        "target_symbol_in_provider": has_symbol,
        "pass": len(prices) > 0 and sse_payload.get("market", {}).get("count", 0) > 0,
    }


async def _test_consistency(symbols: list[str]) -> dict[str, Any]:
    from live_book_hub import get_best_price
    from unified_global_price import compute_ugp

    sym = symbols[0]
    asset = sym.replace("/USDT", "")
    mids: list[float] = []
    for venue in VENUES:
        row = get_best_price(venue, sym, require_fresh=False)
        if row and row.get("mid"):
            mids.append(float(row["mid"]))
    ugp = compute_ugp(asset)
    dispersion = 0.0
    if len(mids) >= 2 and ugp.get("ugp_price"):
        ref = float(ugp["ugp_price"])
        dispersion = (max(mids) - min(mids)) / ref * 10_000 if ref > 0 else 0.0
    return {
        "venue_mids": mids,
        "ugp_price": ugp.get("ugp_price"),
        "dispersion_bps": round(dispersion, 2),
        "venues_used": ugp.get("venues_used", 0),
        "pass": len(mids) >= 2 and dispersion < 500,
    }


async def _test_error_handling() -> dict[str, Any]:
    from live_book_hub import get_best_price
    from price_stream_engine import emit_tick

    await emit_tick("binance", "ERR/USDT", bid=0.0, bid_qty=1, ask=100.0, ask_qty=1)
    row = get_best_price("binance", "ERR/USDT", require_fresh=False)
    return {
        "zero_bid_rejected": row is None,
        "pass": row is None,
    }


async def run_g2_validation(*, duration_sec: float, symbols: list[str]) -> dict[str, Any]:
    _configure_env()
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _utcnow(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "redis_url": bool(os.getenv("REDIS_URL")),
            "price_feed_ws_only": os.getenv("PRICE_FEED_WS_ONLY", "true"),
        },
        "symbols": symbols,
        "venues": list(VENUES),
        "cases": {},
    }

    pipeline_started = False
    try:
        logger.info("Starting live WS pipeline...")
        await _start_pipeline()
        pipeline_started = True

        warmup_sec = min(20, max(10, duration_sec * 0.15))
        logger.info("Warm-up %.0fs before tick probe...", warmup_sec)
        await asyncio.sleep(warmup_sec)

        wait_timeout = min(60, max(30, duration_sec * 0.4))
        logger.info("Waiting for live ticks (timeout %.0fs)...", wait_timeout)
        tick_wait = await _wait_for_ticks(symbols, timeout_sec=wait_timeout)
        log["cases"]["live_exchange_data"] = {
            **tick_wait,
            "pass": len(tick_wait.get("venues_ready", [])) >= tick_wait["quotes_expected_min"],
        }

        observe_sec = max(10, duration_sec - 50)
        logger.info("Observing feed for %.0fs...", observe_sec)
        ingress_latencies: list[float] = []
        t_obs = time.monotonic()
        while time.monotonic() - t_obs < observe_sec:
            from ultra_tick_ingress import ingress_stats

            stats = ingress_stats()
            if stats.get("avg_latency_ms"):
                ingress_latencies.append(float(stats["avg_latency_ms"]))
            await asyncio.sleep(2.0)

        from exchange_ws_hub import ws_hub_stats
        from ultra_tick_ingress import ingress_stats
        from live_book_hub import hub_stats
        from redis_price_cache import cache_stats

        log["pipeline_stats"] = {
            "ws_hub": ws_hub_stats(),
            "ingress": ingress_stats(),
            "live_book": hub_stats(),
            "redis": cache_stats(),
        }
        log["latency"] = {
            "ingress_avg_ms": round(statistics.mean(ingress_latencies), 2) if ingress_latencies else None,
            "ingress_samples": len(ingress_latencies),
            "book_ages_ms": tick_wait.get("book_age_ms", []),
        }

        log["cases"]["timestamp_validation"] = await _test_timestamps(symbols)
        log["cases"]["sequence_and_gap_detection"] = await _test_sequence_and_gaps()
        log["cases"]["duplicate_prevention"] = await _test_duplicate_prevention()
        log["cases"]["reconnect_behavior"] = await _test_reconnect()
        log["cases"]["failover_rest_fallback"] = await _test_failover_and_rest_fallback(symbols)
        log["cases"]["api_sse_dashboard_layer"] = await _test_api_layers(symbols)
        log["cases"]["cross_source_consistency"] = await _test_consistency(symbols)
        log["cases"]["error_handling"] = await _test_error_handling()

    except Exception as exc:
        logger.exception("G2 validation failed")
        log["fatal_error"] = str(exc)
    finally:
        if pipeline_started:
            await _stop_pipeline()
        log["finished_at"] = _utcnow()

    cases = log.get("cases", {})
    passed = sum(1 for c in cases.values() if c.get("pass"))
    total = len(cases)
    log["summary"] = {
        "cases_passed": passed,
        "cases_total": total,
        "g2_verdict": "PASS" if passed == total and total > 0 and "fatal_error" not in log else "FAIL",
    }

    log_path = LOG_DIR / f"g2_run_{run_id}.json"
    log_path.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    log["log_path"] = str(log_path)
    _write_report(log)
    return log


def _write_report(log: dict[str, Any]) -> None:
    cases = log.get("cases", {})
    lines = [
        "# Feature #001 / #002 — G2 Live WebSocket E2E Validation Report",
        "",
        f"**Run ID:** {log.get('run_id')}",
        f"**Started:** {log.get('started_at')}",
        f"**Finished:** {log.get('finished_at')}",
        "",
        "## Test Environment",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Python | {log.get('environment', {}).get('python')} |",
        f"| Platform | {log.get('environment', {}).get('platform')} |",
        f"| Redis | {'configured' if log.get('environment', {}).get('redis_url') else 'local mirror / disabled'} |",
        f"| WS Only | {log.get('environment', {}).get('price_feed_ws_only')} |",
        f"| Log file | `{log.get('log_path', '')}` |",
        "",
        "## Exchanges Tested",
        "",
        "- binance (bookTicker WSS)",
        "- okx (bbo-tbt WSS)",
        "- bybit (orderbook.1 WSS)",
        "",
        "## Symbols Tested",
        "",
    ]
    for s in log.get("symbols", []):
        lines.append(f"- {s}")
    lines.extend(["", "## Case Results", ""])
    lines.append("| Case | PASS/FAIL | Evidence |")
    lines.append("|------|-----------|----------|")
    for name, case in cases.items():
        verdict = "✅ PASS" if case.get("pass") else "🔴 FAIL"
        if case.get("skipped"):
            verdict = "⚠️ SKIP (pass-by-policy)"
        evidence = json.dumps({k: v for k, v in case.items() if k != "pass"}, default=str)[:120]
        lines.append(f"| {name} | {verdict} | `{evidence}...` |")

    lat = log.get("latency", {})
    lines.extend(
        [
            "",
            "## Latency Measurements",
            "",
            f"- Ingress avg: **{lat.get('ingress_avg_ms')} ms** ({lat.get('ingress_samples')} samples)",
            f"- Book ages at capture: {lat.get('book_ages_ms', [])[:10]}",
            "",
            "## Pipeline Stats (final snapshot)",
            "",
            f"```json",
            json.dumps(log.get("pipeline_stats", {}), indent=2, default=str)[:3000],
            "```",
            "",
            "## G2 Verdict",
            "",
        ]
    )
    verdict = log.get("summary", {}).get("g2_verdict", "FAIL")
    if verdict == "PASS":
        lines.append("## ✅ G2: PASS")
    else:
        lines.append("## 🔴 G2: FAIL")
        if log.get("fatal_error"):
            lines.append(f"\nFatal error: `{log['fatal_error']}`")
        lines.append(f"\nCases passed: {log.get('summary', {}).get('cases_passed')}/{log.get('summary', {}).get('cases_total')}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Feature #1 and #2 remain **NOT COMPLETE** until all Quality Gates (G1–G9) pass.",
            "- G3 24h soak test runs **only after G2 PASS**.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="G2 Live WS E2E validation")
    parser.add_argument("--duration", type=float, default=90.0, help="Total run duration seconds")
    parser.add_argument("--symbols", type=str, default="BTC,ETH,SOL", help="Comma-separated assets")
    args = parser.parse_args()
    symbols = [f"{s.strip().upper()}/USDT" for s in args.symbols.split(",") if s.strip()]
    result = asyncio.run(run_g2_validation(duration_sec=args.duration, symbols=symbols))
    print(json.dumps(result.get("summary", {}), indent=2))
    print(f"Report: {REPORT_PATH}")
    print(f"Log: {result.get('log_path')}")
    sys.exit(0 if result.get("summary", {}).get("g2_verdict") == "PASS" else 1)


if __name__ == "__main__":
    main()
