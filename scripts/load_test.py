#!/usr/bin/env python3
"""Simple load test for buyer due diligence (Buyer Requirement #3)."""

from __future__ import annotations

import argparse
import statistics
import time
import urllib.request


def probe(url: str) -> float:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from path_safety import open_http_url
    t0 = time.perf_counter()
    with open_http_url(url, timeout=10) as resp:
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
        (f"{args.base}/health/live", "app_live"),
        (f"{args.base}/health/ready", "ready"),
        (f"{args.base}/api/trust-os", "trust_os"),
        (f"{args.base}/api/strategy/correction", "strategy_correction"),
        (f"{args.base}/oracle-accuracy", "ledger_page"),
        (f"{sidecar}/health/live", "sidecar_live"),
    ]

    print(f"Load test | base={args.base} requests={args.requests}\n")
    any_core_ok = False
    for url, label in endpoints:
        times: list[float] = []
        errors = 0
        for _ in range(args.requests):
            try:
                times.append(probe(url))
            except Exception:
                errors += 1
        if times:
            p95_idx = max(0, int(len(times) * 0.95) - 1)
            print(
                f"  {label}: p50={statistics.median(times):.0f}ms "
                f"p95={sorted(times)[p95_idx]:.0f}ms "
                f"max={max(times):.0f}ms errors={errors}/{args.requests}"
            )
            if label != "sidecar_live":
                any_core_ok = True
        else:
            print(f"  {label}: ALL FAILED ({errors} errors) — optional" if label == "sidecar_live" else f"  {label}: ALL FAILED")
            if label != "sidecar_live":
                return 1

    if not any_core_ok:
        return 1
    print("\nPASS — load test complete (sidecar optional)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
