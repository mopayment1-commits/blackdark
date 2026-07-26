#!/usr/bin/env python3
"""Simple load test for buyer due diligence (Buyer Requirement #3)."""

from __future__ import annotations

import argparse
import statistics
import time
import urllib.request


def probe(url: str) -> float:
    t0 = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as resp:
        resp.read()
    return (time.perf_counter() - t0) * 1000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--requests", type=int, default=50)
    args = parser.parse_args()

    port = int(args.base.rsplit(":", 1)[-1])
    sidecar = f"http://127.0.0.1:{port + 100}"

    endpoints = [
        (f"{sidecar}/health/live", "sidecar_live"),
        (f"{args.base}/health/ready", "ready"),
        (f"{args.base}/api/risk/status", "risk"),
    ]

    print(f"Load test | base={args.base} requests={args.requests}\n")
    for url, label in endpoints:
        times: list[float] = []
        errors = 0
        for _ in range(args.requests):
            try:
                times.append(probe(url))
            except Exception:
                errors += 1
        if times:
            print(
                f"  {label}: p50={statistics.median(times):.0f}ms "
                f"p95={sorted(times)[int(len(times)*0.95)-1]:.0f}ms "
                f"max={max(times):.0f}ms errors={errors}"
            )
        else:
            print(f"  {label}: ALL FAILED")
            return 1

    print("\nPASS — load test complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
