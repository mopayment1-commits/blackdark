"""
BLACKDARK — Latency audit for due diligence (price → algorithmic decision ≤50ms).

Measures the in-memory decision path: live_book_hub (post-WS/API ingest) → fast_scan decision.
"""

from __future__ import annotations

import statistics
import time
from typing import Any

from fast_scan_engine import run_fast_scan
from live_book_hub import hub_stats, update_top_of_book

LATENCY_TARGET_MS = 50.0
DEFAULT_RUNS = 50


def _seed_warm_books() -> None:
    """Simulate fresh API/WS prices in live_book_hub."""
    spreads = (
        ("binance", "BTC", 50000.0, 50010.0),
        ("okx", "BTC", 50020.0, 50030.0),
        ("bybit", "BTC", 50015.0, 50025.0),
        ("binance", "ETH", 3000.0, 3001.0),
        ("okx", "ETH", 3002.0, 3003.0),
        ("bybit", "ETH", 3001.5, 3002.5),
        ("binance", "SOL", 150.0, 150.1),
        ("okx", "SOL", 150.2, 150.3),
        ("bybit", "SOL", 150.15, 150.25),
    )
    for exchange, asset, bid, ask in spreads:
        update_top_of_book(exchange, f"{asset}/USDT", bid=bid, bid_qty=5.0, ask=ask, ask_qty=5.0)


def benchmark_price_to_decision(*, runs: int = DEFAULT_RUNS, seed: bool = True, warmup: int = 5) -> dict[str, Any]:
    """
    Benchmark: price already in live_book_hub → algorithmic spread/fee decision.
    This is the due-diligence latency path (warm, in-memory).
    """
    if seed:
        _seed_warm_books()

    for _ in range(max(0, warmup)):
        run_fast_scan()

    samples: list[float] = []
    last: dict[str, Any] = {}
    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        last = run_fast_scan()
        samples.append((time.perf_counter() - t0) * 1000)

    samples.sort()
    n = len(samples)

    def pct(p: float) -> float:
        if n == 1:
            return round(samples[0], 3)
        idx = min(n - 1, max(0, int(p / 100 * n)))
        return round(samples[idx], 3)

    p50 = pct(50)
    p95 = pct(95)
    p99 = pct(99)
    mx = round(max(samples), 3)
    mn = round(min(samples), 3)
    mean = round(statistics.mean(samples), 3)

    return {
        "path": "live_book_hub -> fast_scan_engine (price-to-decision)",
        "target_ms": LATENCY_TARGET_MS,
        "runs": n,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "min_ms": mn,
        "max_ms": mx,
        "mean_ms": mean,
        "meets_target_p99": p99 <= LATENCY_TARGET_MS,
        "meets_target_p95": p95 <= LATENCY_TARGET_MS,
        "last_scan": {
            "latency_ms": last.get("latency_ms"),
            "latency_tier": last.get("latency_tier"),
            "opportunities": len(last.get("opportunities") or []),
        },
        "books": hub_stats(),
        "disclaimer": (
            "Full Oracle/REST arbitrage paths are slower by design. "
            "Due-diligence SLA applies to this warm in-memory decision path."
        ),
    }


def latency_status() -> dict[str, Any]:
    bench = benchmark_price_to_decision(runs=20, seed=True)
    return {
        **bench,
        "endpoint": "/api/due-diligence/latency",
        "fast_scan_endpoint": "/api/low-latency/fast-scan",
    }
