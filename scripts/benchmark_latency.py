#!/usr/bin/env python3
"""Quick latency benchmark for due-diligence audit."""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    from fast_scan_engine import run_fast_scan

    print("=== FAST SCAN (in-memory) ===")
    for i in range(3):
        t0 = time.perf_counter()
        r = run_fast_scan()
        wall = (time.perf_counter() - t0) * 1000
        print(
            f"  run {i+1}: wall={wall:.3f}ms reported={r.get('latency_ms')}ms "
            f"tier={r.get('latency_tier')} books={r.get('books', {}).get('symbol_count', 0)}"
        )

    print("\n=== FULL ARB SCAN ===")
    from arbitrage_service import scan_arbitrage_opportunities

    for label, prefer_live in [("cache/default", False), ("prefer_live_no_rest", True)]:
        t0 = time.perf_counter()
        r = await scan_arbitrage_opportunities(prefer_live=prefer_live, force_rest=False)
        wall = (time.perf_counter() - t0) * 1000
        print(
            f"  {label}: wall={wall:.1f}ms scan_ms={r.get('scan_ms')} "
            f"source={r.get('data_source')} data_age={r.get('data_age_sec')}s "
            f"opps={len(r.get('opportunities') or [])}"
        )

    print("\n=== MARKET SNAPSHOTS ===")
    from arbitrage_service import get_market_snapshots

    for label, prefer in [("low_latency_path", None), ("prefer_live_true", True)]:
        t0 = time.perf_counter()
        books, funding, source, age = await get_market_snapshots(prefer_live=prefer)
        wall = (time.perf_counter() - t0) * 1000
        venues = len(books)
        symbols = sum(len(v) for v in books.values())
        print(f"  {label}: wall={wall:.1f}ms source={source} age={age:.2f}s venues={venues} symbols={symbols}")

    print("\n=== INSTITUTIONAL CONTEXT ===")
    from whale_tracker import get_latest_institutional_context

    t0 = time.perf_counter()
    ctx = await get_latest_institutional_context()
    wall = (time.perf_counter() - t0) * 1000
    print(f"  whale context: {wall:.1f}ms keys={len(ctx)}")

    print("\n=== OOD GATE (no envelope) ===")
    from ml.drift_monitor import ood_score

    sample = {"price": 50000, "ret_1h": 0.5, "ret_4h": 1.0, "ret_24h": 2.0, "volatility": 0.3}
    ood = ood_score(sample)
    print(f"  ood={ood} (fail_closed expects is_ood=True when no envelope)")

    print("\n=== WARM CACHE SCANS ===")
    for label, prefer_live in [
        ("warm_cache_live_false", False),
        ("warm_cache_live_true", True),
    ]:
        t0 = time.perf_counter()
        r = await scan_arbitrage_opportunities(prefer_live=prefer_live)
        wall = (time.perf_counter() - t0) * 1000
        print(
            f"  {label}: wall={wall:.1f}ms scan_ms={r.get('scan_ms')} "
            f"source={r.get('data_source')} age={r.get('data_age_sec')}s"
        )

    print("\n=== WS WARM PATH ===")
    from live_book_hub import update_top_of_book

    for ex in ("binance", "okx", "bybit"):
        for asset, p in (("BTC", 50000), ("ETH", 3000), ("SOL", 150)):
            update_top_of_book(
                ex, f"{asset}/USDT", bid=p * 0.999, bid_qty=1, ask=p * 1.001, ask_qty=1
            )
    t0 = time.perf_counter()
    r = await scan_arbitrage_opportunities(prefer_live=False)
    wall = (time.perf_counter() - t0) * 1000
    print(
        f"  ws_books_scan: wall={wall:.1f}ms scan_ms={r.get('scan_ms')} "
        f"source={r.get('data_source')} age={r.get('data_age_sec')}s"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
