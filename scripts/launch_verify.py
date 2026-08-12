#!/usr/bin/env python3
"""Pre-launch verification — extends verify_buyer.py with launch checklist gates."""

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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def probe(url: str, label: str) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        safe_url = assert_safe_http_url(url)
        with safe_urlopen(safe_url, timeout=12) as resp:
            ok = resp.status == 200
    except (OSError, ValueError):
        ok = False
    ms = (time.perf_counter() - t0) * 1000
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: {ms:.0f}ms — {url}")
    return ok, ms


def _probe_group(items: list[tuple[str, str]]) -> int:
    ok_count = 0
    for url, label in items:
        ok, _ = probe(url, label)
        if ok:
            ok_count += 1
    return ok_count


def _probe_admin_gates(base: str) -> None:
    for path in ("/admin/launch", "/admin/plan", "/admin/roadmap"):
        try:
            with safe_urlopen(assert_safe_http_url(f"{base}{path}"), timeout=8) as resp:
                print(f"  [WARN] {path} publicly reachable — got {resp.status}")
        except ValueError as exc:
            print(f"  [FAIL] {path} blocked by URL allowlist: {exc}")
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                print(f"  [OK] {path} gated/missing as expected ({exc.code})")
            else:
                print(f"  [WARN] {path} → HTTP {exc.code}")


def _print_launch_checklist() -> dict:
    from launch_checklist import launch_checklist

    lc = launch_checklist()
    print(f"Launch checklist: {lc['done_count']}/{lc['total_tasks']} ({lc['launch_percent']}%)")
    print(f"Blocked: {lc['blocked_count']} · Ready: {'YES' if lc['launch_ready'] else 'NOT YET'}")
    if lc.get("next_actions"):
        print("\nNext actions:")
        for action in lc["next_actions"][:6]:
            print(f"  • [{action['status']}] {action.get('title', action.get('id', ''))}: {action['action']}")
    return lc


def main() -> int:
    base = assert_safe_http_url(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080")

    print(f"BLACKDARK LAUNCH VERIFY | {base}\n")

    pages = [
        (f"{base}/", "landing"),
        (f"{base}/dashboard", "dashboard"),
        (f"{base}/platform", "platform"),
        (f"{base}/login", "login"),
        (f"{base}/terms", "terms"),
        (f"{base}/manifest.json", "pwa manifest"),
    ]
    apis = [
        (f"{base}/health/live", "liveness"),
        (f"{base}/health/ready", "readiness"),
        (f"{base}/api/services/status", "services"),
        (f"{base}/api/billing/status", "billing"),
        (f"{base}/api/arbitrage/opportunities", "arbitrage"),
    ]
    total = len(pages) + len(apis)
    ok_count = _probe_group(pages + apis)

    # Admin launch page is gated (403 without admin) — must NOT be a public 200
    _probe_admin_gates(base)

    # Constitution product probes
    constitution_apis = [
        (f"{base}/oracle/BTC?ux_mode=beginner&lang=en", "oracle_beginner_en"),
        (f"{base}/api/oracle/accuracy/public", "public_accuracy"),
        (f"{base}/api/oracle/net-edge-truth", "net_edge_truth"),
        (f"{base}/api/oracle/half-life", "half_life"),
        (f"{base}/api/due-diligence/evidence-pack/public-summary", "evidence_public"),
        (f"{base}/oracle-accuracy", "accuracy_page"),
    ]
    ok_count += _probe_group(constitution_apis)
    total += len(constitution_apis)

    print()
    lc = _print_launch_checklist()

    pass_rate = ok_count / total if total else 0
    if pass_rate < 0.85:
        print(f"\nFAIL — HTTP checks {ok_count}/{total}")
        return 1
    print("\nPASS — launch verification OK (fix blocked checklist items before go-live)")
    return 0 if lc["blocked_count"] <= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
