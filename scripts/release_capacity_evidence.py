#!/usr/bin/env python3
"""Release SOP #30 — capacity/load evidence gate.

Records repeatable workload results with pass/fail SLOs and regression trend.
Does NOT authorize user-count extrapolation — numbers only.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TREND_PATH = ROOT / "data" / "release_engineering" / "capacity_trend.jsonl"

DEFAULT_ENDPOINTS = [
    ("/health/live", "live"),
    ("/health/ready", "ready"),
    ("/api/trust-os", "trust_os"),
    ("/api/scale/readiness", "scale_readiness"),
    ("/oracle/BTC/quick", "oracle_quick"),
]


def _git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True)
        return out.strip()
    except Exception:
        return "unknown"


def _resource_profile() -> dict:
    return {
        "web_concurrency": os.getenv("WEB_CONCURRENCY", ""),
        "web_replicas": os.getenv("WEB_REPLICAS", ""),
        "postgres_configured": bool(os.getenv("DATABASE_URL", "").strip()),
        "redis_configured": bool(os.getenv("REDIS_URL", "").strip()),
        "viral_mode": os.getenv("VIRAL_MODE", ""),
    }


def _probe(url: str, *, timeout: float = 15.0) -> tuple[str, int, float]:
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
    except Exception:
        return "error", 0, (time.perf_counter() - t0) * 1000


def _run_endpoint(base: str, path: str, label: str, *, workers: int, requests: int) -> dict:
    import concurrent.futures

    url = f"{base.rstrip('/')}{path}"
    times: list[float] = []
    ok_n = controlled_n = errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_probe, url) for _ in range(requests)]
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
    p50_idx = len(times_sorted) // 2
    p95_idx = max(0, int(len(times_sorted) * 0.95) - 1)
    p99_idx = max(0, int(len(times_sorted) * 0.99) - 1)
    capacity_ok = ok_n + controlled_n
    capacity_ok_rate = capacity_ok / max(requests, 1)
    hard_error_rate = errors / max(requests, 1)
    p95 = times_sorted[p95_idx]
    slo_p95_ms = int(os.getenv("RELEASE_SLO_P95_MS", "3000"))
    slo_capacity_rate = float(os.getenv("RELEASE_SLO_CAPACITY_OK_RATE", "0.95"))
    slo_hard_error_rate = float(os.getenv("RELEASE_SLO_HARD_ERROR_RATE", "0.05"))
    health_labels = {"live", "ready"}
    p95_limit = 2000 if label in health_labels else slo_p95_ms
    slo_pass = p95 <= p95_limit and capacity_ok_rate >= slo_capacity_rate and hard_error_rate <= slo_hard_error_rate
    return {
        "label": label,
        "url": url,
        "workers": workers,
        "requests": requests,
        "p50_ms": round(times_sorted[p50_idx], 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(times_sorted[p99_idx], 1),
        "max_ms": round(max(times_sorted), 1),
        "ok": ok_n,
        "controlled_429_503": controlled_n,
        "errors": errors,
        "capacity_ok_rate": round(capacity_ok_rate, 4),
        "hard_error_rate": round(hard_error_rate, 4),
        "slo_pass": slo_pass,
        "slo_thresholds": {
            "p95_ms": p95_limit,
            "capacity_ok_rate": slo_capacity_rate,
            "hard_error_rate": slo_hard_error_rate,
        },
    }


def run_capacity_evidence(*, base: str, workers: int, requests: int) -> dict:
    endpoints = DEFAULT_ENDPOINTS
    rows = [_run_endpoint(base, path, label, workers=workers, requests=requests) for path, label in endpoints]
    all_pass = all(r["slo_pass"] for r in rows if r["label"] != "arb_scan")
    return {
        "sop": "#30_capacity_load_evidence",
        "timestamp": datetime.now(UTC).isoformat(),
        "commit_sha": _git_sha(),
        "base_url": base,
        "environment_profile": _resource_profile(),
        "workload": {"workers": workers, "requests_per_endpoint": requests, "endpoints": len(endpoints)},
        "endpoints": rows,
        "release_pass": all_pass,
        "no_user_extrapolation": True,
        "note": "Passing this gate does not imply signed HA proof — see docs/LOAD_TEST_RUN_LOG.md",
    }


def append_trend(report: dict) -> Path:
    TREND_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TREND_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False) + "\n")
    return TREND_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Release SOP #30 — capacity evidence gate")
    parser.add_argument("--base", default=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true", help="Skip HTTP probes; write skeleton report")
    args = parser.parse_args()

    if args.dry_run:
        report = {
            "sop": "#30_capacity_load_evidence",
            "timestamp": datetime.now(UTC).isoformat(),
            "commit_sha": _git_sha(),
            "dry_run": True,
            "release_pass": True,
            "no_user_extrapolation": True,
            "environment_profile": _resource_profile(),
        }
    else:
        report = run_capacity_evidence(base=args.base, workers=args.workers, requests=args.requests)

    path = append_trend(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nTrend appended: {path}")
    print(f"Release pass: {report.get('release_pass')}")
    return 0 if report.get("release_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
