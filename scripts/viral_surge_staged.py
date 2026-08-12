#!/usr/bin/env python3
"""Staged viral surge / concurrency kill-gate harness.

Progressive stages A→E plus recovery. Measures latency, error/429 rates, and
process health. Controlled 429/503 count as capacity protection — not collapse.

Does NOT authorize marketing HA numbers beyond what this environment proves.
Append results to docs/LOAD_TEST_RUN_LOG.md and docs/dd/VIRAL_SURGE_EVIDENCE.md.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import resource
import statistics
import subprocess
import sys
import time
import urllib.error
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from path_safety import open_http_url  # noqa: E402


STAGES = {
    "A": {"name": "baseline", "workers": 10, "requests": 40, "hold_sec": 0},
    "B": {"name": "2x", "workers": 20, "requests": 80, "hold_sec": 0},
    "C": {"name": "5x", "workers": 50, "requests": 150, "hold_sec": 0},
    "D": {"name": "10x", "workers": 100, "requests": 250, "hold_sec": 0},
    "E": {"name": "viral_burst", "workers": 200, "requests": 400, "hold_sec": 0},
}


@dataclass
class ProbeAgg:
    label: str
    workers: int
    requests: int
    ok: int = 0
    controlled: int = 0
    errors: int = 0
    timeouts: int = 0
    statuses: dict[str, int] = field(default_factory=dict)
    latencies_ms: list[float] = field(default_factory=list)

    def finalize(self) -> dict[str, Any]:
        times = sorted(self.latencies_ms) or [0.0]
        n = max(self.requests, 1)

        def pct(p: float) -> float:
            if not times:
                return 0.0
            idx = min(len(times) - 1, max(0, int(len(times) * p) - 1))
            return round(times[idx], 1)

        capacity_ok = self.ok + self.controlled
        return {
            "label": self.label,
            "workers": self.workers,
            "requests": self.requests,
            "ok": self.ok,
            "controlled_429_503": self.controlled,
            "errors": self.errors,
            "timeouts": self.timeouts,
            "statuses": dict(self.statuses),
            "p50_ms": pct(0.50),
            "p95_ms": pct(0.95),
            "p99_ms": pct(0.99),
            "max_ms": round(max(times), 1),
            "rps": round(n / max((sum(times) / 1000.0) / max(self.workers, 1), 0.001), 1),
            "ok_rate": round(self.ok / n, 4),
            "controlled_rate": round(self.controlled / n, 4),
            "error_rate": round(self.errors / n, 4),
            "capacity_ok_rate": round(capacity_ok / n, 4),
        }


def _probe(url: str, timeout: float) -> tuple[str, int, float]:
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
    except TimeoutError:
        return "timeout", 0, (time.perf_counter() - t0) * 1000
    except Exception as exc:
        msg = str(exc).lower()
        kind = "timeout" if "timed out" in msg or "timeout" in msg else "error"
        return kind, 0, (time.perf_counter() - t0) * 1000


def _run_endpoint(url: str, label: str, workers: int, requests: int, timeout: float) -> dict[str, Any]:
    agg = ProbeAgg(label=label, workers=workers, requests=requests)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_probe, url, timeout) for _ in range(requests)]
        for fut in concurrent.futures.as_completed(futs):
            kind, status, ms = fut.result()
            agg.latencies_ms.append(ms)
            key = str(status)
            agg.statuses[key] = agg.statuses.get(key, 0) + 1
            if kind == "ok":
                agg.ok += 1
            elif kind == "controlled":
                agg.controlled += 1
            elif kind == "timeout":
                agg.timeouts += 1
                agg.errors += 1
            else:
                agg.errors += 1
    return agg.finalize()


def _fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any] | None:
    try:
        with open_http_url(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _sample_host() -> dict[str, Any]:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    mem = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith(("MemAvailable:", "MemTotal:", "MemFree:")):
                    k, v, *_ = line.split()
                    mem[k.rstrip(":")] = int(v)
    except OSError:
        pass
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    return {
        "loadavg": list(load),
        "meminfo_kb": mem,
        "harness_ru_maxrss_kb": getattr(ru, "ru_maxrss", 0),
    }


def _sample_redis() -> dict[str, Any]:
    try:
        import redis

        url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
        client = redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
        info = client.info()
        return {
            "ok": True,
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
            "rejected_connections": info.get("rejected_connections"),
        }
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def _sample_postgres() -> dict[str, Any]:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url.startswith("postgres"):
        return {"ok": False, "error": "DATABASE_URL unset"}
    try:
        # Prefer libpq via psql (no extra Python dep). Parse DSN lightly.
        # postgresql://user:pass@host:port/db
        from urllib.parse import urlparse

        parsed = urlparse(url)
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        host = parsed.hostname or "127.0.0.1"
        port = str(parsed.port or 5432)
        user = parsed.username or "blackdark"
        db = (parsed.path or "/blackdark").lstrip("/") or "blackdark"
        sql = (
            "SELECT "
            "(SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()),"
            "(SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
            "AND state = 'active'),"
            "(SELECT setting::int FROM pg_settings WHERE name = 'max_connections');"
        )
        out = subprocess.check_output(
            ["psql", "-h", host, "-p", port, "-U", user, "-d", db, "-t", "-A", "-c", sql],
            env=env,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        parts = out.split("|")
        connections = int(parts[0])
        active = int(parts[1])
        max_conn = int(parts[2])
        return {
            "ok": True,
            "connections": connections,
            "active": active,
            "max_connections": max_conn,
            "saturation_pct": round(100.0 * connections / max(max_conn, 1), 1),
        }
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def _endpoints(base: str) -> list[tuple[str, str]]:
    return [
        (f"{base}/health/live", "live"),
        (f"{base}/health/ready", "ready"),
        (f"{base}/health/viral", "viral_health"),
        (f"{base}/", "landing"),
        (f"{base}/api/trust-os", "trust_os"),
        (f"{base}/api/viral/readiness", "viral_readiness"),
        (f"{base}/api/scale/readiness", "scale_readiness"),
        (f"{base}/oracle/BTC/quick", "oracle_quick"),
        # GET catalog scan (POST /api/arbitrage/scan is mutative / method-bound)
        (f"{base}/api/arbitrage/catalog/scan", "arb_scan"),
        (f"{base}/compliance", "compliance_html"),
    ]


def run_stage(
    base: str,
    stage_id: str,
    *,
    timeout: float,
    only: set[str] | None = None,
) -> dict[str, Any]:
    cfg = STAGES[stage_id]
    workers = int(cfg["workers"])
    requests = int(cfg["requests"])
    print(
        f"\n=== Stage {stage_id} ({cfg['name']}) "
        f"workers={workers} requests/endpoint={requests} ==="
    )
    before = {
        "host": _sample_host(),
        "redis": _sample_redis(),
        "postgres": _sample_postgres(),
        "viral": _fetch_json(f"{base}/api/viral/readiness"),
        "health_viral": _fetch_json(f"{base}/health/viral"),
    }
    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for url, label in _endpoints(base):
        if only and label not in only:
            continue
        row = _run_endpoint(url, label, workers, requests, timeout)
        rows.append(row)
        print(
            f"  {label}: p50={row['p50_ms']} p95={row['p95_ms']} p99={row['p99_ms']} "
            f"ok={row['ok']} ctl={row['controlled_429_503']} err={row['errors']} "
            f"cap_ok={row['capacity_ok_rate']}"
        )
    elapsed = time.perf_counter() - t0
    after = {
        "host": _sample_host(),
        "redis": _sample_redis(),
        "postgres": _sample_postgres(),
        "viral": _fetch_json(f"{base}/api/viral/readiness"),
        "health_viral": _fetch_json(f"{base}/health/viral"),
    }
    # Stage health: core live/ready must stay capacity-ok; hard errors must stay low.
    core = [r for r in rows if r["label"] in {"live", "ready"}]
    hard_collapse = any(r["error_rate"] > 0.05 and r["capacity_ok_rate"] < 0.90 for r in core)
    any_core_cap_fail = any(r["capacity_ok_rate"] < 0.95 for r in core)
    return {
        "stage": stage_id,
        "name": cfg["name"],
        "workers": workers,
        "requests_per_endpoint": requests,
        "elapsed_sec": round(elapsed, 2),
        "endpoints": rows,
        "before": before,
        "after": after,
        "collapse": hard_collapse,
        "core_capacity_fail": any_core_cap_fail,
    }


def run_recovery(
    base: str,
    baseline_p95: dict[str, float],
    *,
    timeout: float,
    settle_sec: float = 65.0,
) -> dict[str, Any]:
    """Wait for per-minute RL windows to drain, then re-probe core + product routes."""
    print(f"\n=== Recovery (post-surge settle {settle_sec:.0f}s) ===")
    time.sleep(max(0.0, settle_sec))
    rows = []
    for url, label in _endpoints(base):
        if label not in {"live", "ready", "trust_os", "oracle_quick", "viral_readiness", "landing"}:
            continue
        row = _run_endpoint(url, label, workers=8, requests=24, timeout=timeout)
        rows.append(row)
        base_p95 = baseline_p95.get(label)
        note = ""
        if base_p95 is not None:
            note = f" baseline_p95={base_p95}"
        print(
            f"  {label}: p50={row['p50_ms']} p95={row['p95_ms']} "
            f"ok_rate={row['ok_rate']} ctl_rate={row['controlled_rate']} "
            f"err={row['errors']}{note}"
        )
    redis = _sample_redis()
    pg = _sample_postgres()
    live = next((r for r in rows if r["label"] == "live"), None)
    ready = next((r for r in rows if r["label"] == "ready"), None)
    trust = next((r for r in rows if r["label"] == "trust_os"), None)
    landing = next((r for r in rows if r["label"] == "landing"), None)
    recovered = True
    reasons: list[str] = []
    if not live or live["ok_rate"] < 0.99:
        recovered = False
        reasons.append("live_not_baseline")
    if not ready or ready["capacity_ok_rate"] < 0.95:
        recovered = False
        reasons.append("ready_not_baseline")
    if live and baseline_p95.get("live") and live["p95_ms"] > max(500.0, baseline_p95["live"] * 5):
        recovered = False
        reasons.append("live_p95_not_recovered")
    # Product routes must regain non-zero 2xx after RL window (not stuck shedding).
    if trust is not None and trust["ok_rate"] < 0.5:
        recovered = False
        reasons.append("trust_os_still_shedding")
    if landing is not None and landing["ok_rate"] < 0.5:
        recovered = False
        reasons.append("landing_still_shedding")
    if pg.get("ok") and float(pg.get("saturation_pct") or 0) > 80:
        recovered = False
        reasons.append("pg_still_saturated")
    return {
        "recovered": recovered,
        "reasons": reasons,
        "settle_sec": settle_sec,
        "endpoints": rows,
        "redis": redis,
        "postgres": pg,
    }


def classify_envelope(stages: list[dict[str, Any]]) -> dict[str, Any]:
    safe = None
    degraded = None
    failure = None
    bottleneck = "unknown"
    product_labels = {"landing", "trust_os", "oracle_quick", "compliance_html"}
    for st in stages:
        workers = st["workers"]
        core_fail = st.get("core_capacity_fail") or st.get("collapse")
        product = [r for r in st["endpoints"] if r["label"] in product_labels]
        product_okish = all(r["capacity_ok_rate"] >= 0.95 for r in product) if product else True
        # "Comfortable" = majority of product routes still returning 2xx (not shed)
        product_mostly_2xx = (
            (sum(1 for r in product if r["ok_rate"] >= 0.5) / max(len(product), 1)) >= 0.5
            if product
            else True
        )
        if st.get("collapse"):
            failure = failure or workers
            bottleneck = "web_or_dependency_collapse"
            break
        if core_fail or not product_okish:
            failure = failure or workers
            bottleneck = "core_or_product_capacity"
            break
        if product_mostly_2xx:
            safe = workers if safe is None else max(safe, workers)
        else:
            degraded = workers if degraded is None else max(degraded, workers)
            bottleneck = "viral_rate_limit_or_oracle_compute"
    if degraded is None and safe is not None:
        # Highest stable stage without collapse still counts as degraded ceiling
        degraded = max(s["workers"] for s in stages if not s.get("collapse"))
    return {
        "SAFE_VERIFIED_CAPACITY_CONCURRENT_WORKERS": safe,
        "DEGRADED_BUT_STABLE_CAPACITY_CONCURRENT_WORKERS": degraded,
        "FAILURE_SATURATION_POINT_CONCURRENT_WORKERS": failure,
        "BOTTLENECK": bottleneck,
        "unit_note": (
            "Numbers are concurrent HTTP worker threads in this harness against "
            "the measured process topology — NOT unique human users, NOT global CDN."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BLACKDARK staged viral surge harness")
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--stages",
        default="A,B,C,D,E",
        help="Comma-separated stage ids (default A,B,C,D,E)",
    )
    parser.add_argument(
        "--out",
        default="docs/dd/VIRAL_SURGE_EVIDENCE.json",
        help="JSON evidence output path",
    )
    parser.add_argument(
        "--stop-on-collapse",
        action="store_true",
        help="Stop escalating after first collapse",
    )
    parser.add_argument(
        "--recovery-settle-sec",
        type=float,
        default=65.0,
        help="Seconds to wait after surge before recovery probes (RL window)",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    stage_ids = [s.strip().upper() for s in args.stages.split(",") if s.strip()]

    viral = _fetch_json(f"{base}/api/viral/readiness")
    health = _fetch_json(f"{base}/health/live")
    if health is None and _probe(f"{base}/health/live", args.timeout)[0] != "ok":
        print(f"FAIL: target not reachable at {base}/health/live")
        return 2

    print(
        f"Viral surge harness | base={base} stages={stage_ids}\n"
        f"Viral readiness: {json.dumps({k: viral.get(k) for k in ('viral_production_approved','viral_codepath_ready','rate_limit_backend','inflight_backend','parallelism')}, default=str) if viral else 'unavailable'}"
    )

    results: list[dict[str, Any]] = []
    baseline_p95: dict[str, float] = {}
    for sid in stage_ids:
        if sid not in STAGES:
            print(f"Unknown stage {sid}")
            return 2
        st = run_stage(base, sid, timeout=args.timeout)
        results.append(st)
        if sid == "A":
            baseline_p95 = {r["label"]: r["p95_ms"] for r in st["endpoints"]}
        if st.get("collapse") and args.stop_on_collapse:
            print("Collapse detected — stopping escalation")
            break

    recovery = run_recovery(
        base,
        baseline_p95,
        timeout=args.timeout,
        settle_sec=args.recovery_settle_sec,
    )
    envelope = classify_envelope(results)

    collapse_any = any(s.get("collapse") for s in results)
    core_fail_any = any(s.get("core_capacity_fail") for s in results)
    # READY requires: no collapse, recovery proven, safe capacity known, controlled degradation present
    ready = (
        not collapse_any
        and not core_fail_any
        and recovery.get("recovered") is True
        and envelope.get("SAFE_VERIFIED_CAPACITY_CONCURRENT_WORKERS") not in {None}
    )
    # Topology honesty: multi-worker + redis required for VIRAL SURGE READY claim
    parallelism = 1
    if viral and isinstance(viral.get("parallelism"), dict):
        parallelism = int(viral["parallelism"].get("parallelism") or 1)
    elif viral and isinstance(viral.get("parallelism"), int):
        parallelism = int(viral["parallelism"])
    redis_ok = bool(viral and viral.get("rate_limit_backend") == "redis")
    topology_ok = parallelism >= 2 and redis_ok
    if not topology_ok:
        ready = False

    verdict = "VIRAL SURGE READY" if ready else "VIRAL SURGE NOT READY"
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "base": base,
        "viral_readiness": viral,
        "stages": results,
        "recovery": recovery,
        "capacity_envelope": envelope,
        "topology": {
            "parallelism": parallelism,
            "redis_shared": redis_ok,
            "topology_ok_for_viral_claim": topology_ok,
        },
        "verdict": verdict,
        "ready_requirements": {
            "no_platform_wide_collapse": not collapse_any,
            "core_health_capacity_ok": not core_fail_any,
            "recovery_proven": recovery.get("recovered"),
            "safe_capacity_measured": envelope.get("SAFE_VERIFIED_CAPACITY_CONCURRENT_WORKERS") is not None,
            "multi_worker_redis_topology": topology_ok,
        },
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"CAPACITY ENVELOPE: {json.dumps(envelope, indent=2)}")
    print(f"VERDICT: {verdict}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
