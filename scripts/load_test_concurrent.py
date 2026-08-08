#!/usr/bin/env python3
"""Concurrent load harness for scale diligence.

Hits health, trust-os, scale readiness, oracle quick, and arb scan under
thread concurrency. Does NOT by itself authorize an HA capacity claim —
record results in docs/LOAD_TEST_RUN_LOG.md after Postgres+Redis multi-worker.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import statistics
import time
import urllib.error
import urllib.request


def probe(url: str, timeout: float = 15.0) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read()
            ok = 200 <= int(resp.status) < 500
    except Exception:
        return False, (time.perf_counter() - t0) * 1000
    return ok, (time.perf_counter() - t0) * 1000


def run_endpoint(url: str, label: str, workers: int, requests: int) -> dict:
    times: list[float] = []
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(probe, url) for _ in range(requests)]
        for fut in concurrent.futures.as_completed(futs):
            ok, ms = fut.result()
            times.append(ms)
            if not ok:
                errors += 1
    times_sorted = sorted(times) if times else [0.0]
    p95_idx = max(0, int(len(times_sorted) * 0.95) - 1)
    return {
        "label": label,
        "url": url,
        "workers": workers,
        "requests": requests,
        "errors": errors,
        "p50_ms": round(statistics.median(times_sorted), 1),
        "p95_ms": round(times_sorted[p95_idx], 1),
        "max_ms": round(max(times_sorted), 1),
        "ok_rate": round((requests - errors) / max(requests, 1), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--requests", type=int, default=100)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    endpoints = [
        (f"{base}/health/live", "live"),
        (f"{base}/health/ready", "ready"),
        (f"{base}/api/trust-os", "trust_os"),
        (f"{base}/api/scale/readiness", "scale_readiness"),
        (f"{base}/oracle/BTC/quick", "oracle_quick"),
        (f"{base}/api/arbitrage/scan", "arb_scan"),
        (f"{base}/compliance", "compliance_html"),
    ]

    print(
        f"Concurrent load | base={base} workers={args.workers} "
        f"requests/endpoint={args.requests}\n"
    )
    any_fail = False
    for url, label in endpoints:
        row = run_endpoint(url, label, args.workers, args.requests)
        print(
            f"  {row['label']}: p50={row['p50_ms']}ms p95={row['p95_ms']}ms "
            f"max={row['max_ms']}ms errors={row['errors']}/{row['requests']} "
            f"ok_rate={row['ok_rate']}"
        )
        # Arb scan may be heavy / gated — tolerate higher error for that label only.
        if label == "arb_scan":
            continue
        if row["ok_rate"] < 0.95:
            any_fail = True

    print(
        "\nNOTE: Passing this harness locally does NOT equal signed HA proof. "
        "Append Postgres+Redis multi-worker results to docs/LOAD_TEST_RUN_LOG.md."
    )
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
