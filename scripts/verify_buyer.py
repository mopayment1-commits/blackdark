#!/usr/bin/env python3
"""Quick buyer verification — health probes + service status (<5s total)."""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import encoding_bootstrap  # noqa: F401
from path_safety import assert_safe_http_url, safe_urlopen


def probe(url: str, label: str) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        safe_url = assert_safe_http_url(url)
        with safe_urlopen(safe_url, timeout=10) as resp:
            ok = resp.status == 200
    except (OSError, ValueError):
        ok = False
    elapsed_ms = (time.perf_counter() - t0) * 1000
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}: {elapsed_ms:.0f}ms — {url}")
    return ok, elapsed_ms


def main() -> int:
    base = assert_safe_http_url(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080")
    try:
        port = int(base.rsplit(":", 1)[-1])
        sidecar = assert_safe_http_url(f"http://127.0.0.1:{port + 100}")
    except ValueError:
        sidecar = base

    print(f"BLACKDARK buyer verify | app={base} sidecar={sidecar}\n")

    # Warm TCP connection to sidecar (subsequent probes target <50ms)
    probe(f"{sidecar}/health/live", "warmup")

    t_start = time.perf_counter()
    checks = [
        probe(f"{sidecar}/health/live", "liveness (sidecar)"),
        probe(f"{base}/health/ready", "readiness"),
        probe(f"{base}/api/services/status", "services"),
    ]
    total_ms = (time.perf_counter() - t_start) * 1000

    _live_ok, live_ms = checks[0]
    all_ok = all(c[0] for c in checks)
    print(f"\nTotal: {total_ms:.0f}ms | live probe: {live_ms:.0f}ms")
    if live_ms > 100:
        print("WARN: sidecar liveness >100ms — check port binding")
    if not all_ok:
        print("Some checks failed — start server: python run_service.py all")
        return 1
    print("PASS — buyer verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
