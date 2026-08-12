#!/usr/bin/env python3
"""Concurrent load harness for scale diligence.

Hits health, trust-os, scale readiness, oracle quick, and arb scan under
thread concurrency. Does NOT by itself authorize an HA capacity claim —
record results in docs/LOAD_TEST_RUN_LOG.md after Postgres+Redis multi-worker.

Controlled degradation (429 / 503) is scored as capacity protection — not a
hard failure — unless --strict-2xx is set.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request


def probe(url: str, timeout: float = 15.0) -> tuple[str, int, float]:
    """Return (class, status, ms). class: ok | controlled | error."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from path_safety import open_http_url

    t0 = time.perf_counter()
    try:
        with open_http_url(url, timeout=timeout) as resp:
            resp.read()
            status = int(resp.status)
            ms = (time.perf_counter() - t0) * 1000
            if 200 <= status < 400:
                return "ok", status, ms
            if status in {429, 503}:
                return "controlled", status, ms
            return "error", status, ms
    except urllib.error.HTTPError as exc:
        ms = (time.perf_counter() - t0) * 1000
        status = int(exc.code)
        if status in {429, 503}:
            return "controlled", status, ms
        return "error", status, ms
    except Exception:
        return "error", 0, (time.perf_counter() - t0) * 1000


def run_endpoint(url: str, label: str, workers: int, requests: int) -> dict:
    times: list[float] = []
    ok_n = 0
    controlled_n = 0
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(probe, url) for _ in range(requests)]
        for fut in concurrent.futures.as_completed(futs):
            kind, _status, ms = fut.result()
            times.append(ms)
            if kind == "ok":
                ok_n += 1
            elif kind == "controlled":
                controlled_n += 1
            else:
                errors += 1
    times_sorted = sorted(times) if times else [0.0]
    p95_idx = max(0, int(len(times_sorted) * 0.95) - 1)
    # Capacity success: 2xx OR controlled degradation (not collapse/timeouts)
    capacity_ok = ok_n + controlled_n
    return {
        "label": label,
        "url": url,
        "workers": workers,
        "requests": requests,
        "ok": ok_n,
        "controlled_429_503": controlled_n,
        "errors": errors,
        "p50_ms": round(statistics.median(times_sorted), 1),
        "p95_ms": round(times_sorted[p95_idx], 1),
        "max_ms": round(max(times_sorted), 1),
        "ok_rate": round(ok_n / max(requests, 1), 4),
        "capacity_ok_rate": round(capacity_ok / max(requests, 1), 4),
    }


def fetch_json(url: str) -> dict | None:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from path_safety import open_http_url

    try:
        with open_http_url(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument(
        "--strict-2xx",
        action="store_true",
        help="Treat 429/503 as failures (default: controlled degradation OK)",
    )
    parser.add_argument(
        "--require-viral-approved",
        action="store_true",
        help="Fail if /api/viral/readiness viral_production_approved is not true",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")

    viral = fetch_json(f"{base}/api/viral/readiness")
    if viral is not None:
        print(
            "Viral readiness: approved="
            f"{viral.get('viral_production_approved')} "
            f"codepath={viral.get('viral_codepath_ready')} "
            f"redis={viral.get('rate_limit_backend')} "
            f"parallelism={viral.get('parallelism')}"
        )
        if args.require_viral_approved and not viral.get("viral_production_approved"):
            print("FAIL: viral_production_approved is false — refuse load claim")
            return 2

    endpoints = [
        (f"{base}/health/live", "live"),
        (f"{base}/health/ready", "ready"),
        (f"{base}/health/viral", "viral_health"),
        (f"{base}/api/trust-os", "trust_os"),
        (f"{base}/api/scale/readiness", "scale_readiness"),
        (f"{base}/api/viral/readiness", "viral_readiness"),
        (f"{base}/oracle/BTC/quick", "oracle_quick"),
        (f"{base}/api/arbitrage/scan", "arb_scan"),
        (f"{base}/compliance", "compliance_html"),
    ]

    print(
        f"Concurrent load | base={base} workers={args.workers} "
        f"requests/endpoint={args.requests} strict_2xx={args.strict_2xx}\n"
    )
    any_fail = False
    for url, label in endpoints:
        row = run_endpoint(url, label, args.workers, args.requests)
        print(
            f"  {row['label']}: p50={row['p50_ms']}ms p95={row['p95_ms']}ms "
            f"max={row['max_ms']}ms ok={row['ok']} controlled={row['controlled_429_503']} "
            f"errors={row['errors']}/{row['requests']} "
            f"ok_rate={row['ok_rate']} capacity_ok_rate={row['capacity_ok_rate']}"
        )
        if label == "arb_scan":
            continue
        metric = row["ok_rate"] if args.strict_2xx else row["capacity_ok_rate"]
        if metric < 0.95:
            any_fail = True

    print(
        "\nNOTE: Passing this harness does NOT equal signed HA proof. "
        "Append Postgres+Redis multi-worker results to docs/LOAD_TEST_RUN_LOG.md. "
        "429/503 count as controlled degradation unless --strict-2xx."
    )
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
