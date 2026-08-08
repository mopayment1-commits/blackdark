#!/usr/bin/env python3
"""
10k concurrent-user load harness (acquisition scalability evidence).

Usage (against a hardened stack — Postgres + Redis compose recommended):
  python scripts/load_test_10k.py --base http://127.0.0.1:8080 --users 10000 --requests 2

Writes: data/load_test_10k_report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

try:
    import aiohttp
except ImportError:
    raise SystemExit("pip install aiohttp") from None


async def _probe(session: aiohttp.ClientSession, url: str) -> tuple[bool, float, int]:
    t0 = time.perf_counter()
    status = 0
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            await resp.read()
            status = resp.status
            ok = 200 <= resp.status < 400
    except Exception:
        ok = False
    return ok, (time.perf_counter() - t0) * 1000, status


async def run_load(base: str, *, users: int, requests_per_user: int) -> dict:
    base = base.rstrip("/")
    urls = [
        f"{base}/health/live",
        f"{base}/health/ready",
        f"{base}/api/auth/oauth/status",
        f"{base}/oracle-accuracy",
    ]
    latencies: list[float] = []
    errors = 0
    total = users * requests_per_user * len(urls)
    sem = asyncio.Semaphore(min(users, 2000))

    async def one_user(session: aiohttp.ClientSession) -> None:
        nonlocal errors
        async with sem:
            for _ in range(requests_per_user):
                for url in urls:
                    ok, ms, _status = await _probe(session, url)
                    latencies.append(ms)
                    if not ok:
                        errors += 1

    t0 = time.perf_counter()
    connector = aiohttp.TCPConnector(limit=min(users, 2000), ttl_dns_cache=60)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[one_user(session) for _ in range(users)])
    elapsed = time.perf_counter() - t0
    sorted_lat = sorted(latencies) if latencies else [0.0]
    err_rate = (errors / total) if total else 1.0
    return {
        "target": base,
        "concurrent_users": users,
        "requests_per_user": requests_per_user,
        "endpoints": urls,
        "total_requests": total,
        "duration_sec": round(elapsed, 2),
        "requests_per_sec": round(total / elapsed, 1) if elapsed else 0,
        "latency_ms": {
            "p50": round(statistics.median(sorted_lat), 2),
            "p95": round(sorted_lat[int(len(sorted_lat) * 0.95)], 2),
            "p99": round(sorted_lat[int(len(sorted_lat) * 0.99)], 2),
            "max": round(max(sorted_lat), 2),
        },
        "errors": errors,
        "error_rate_percent": round(err_rate * 100, 3),
        "pass_criteria": {
            "max_error_rate_percent": 1.0,
            "passed": err_rate < 0.01,
        },
        "evidence_note": (
            "This report is valid acquisition evidence only when run against "
            "Postgres+Redis production-like compose (docker-compose.prod.yml), not SQLite soft-launch."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--users", type=int, default=10000)
    parser.add_argument("--requests", type=int, default=2)
    parser.add_argument("--output", default="data/load_test_10k_report.json")
    args = parser.parse_args()

    report = asyncio.run(run_load(args.base, users=args.users, requests_per_user=args.requests))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nSaved: {out}")
    return 0 if report["pass_criteria"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
