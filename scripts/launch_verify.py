#!/usr/bin/env python3
"""Pre-launch verification — extends verify_buyer.py with launch checklist gates."""

from __future__ import annotations

import os
import sys
import time
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import encoding_bootstrap  # noqa: F401
from path_safety import assert_safe_http_url, safe_urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_DEFAULT_PROBE_TIMEOUT = 30.0


def _load_launch_env_hosts() -> set[str]:
    hosts: set[str] = set()
    path = ROOT / ".env.launch.local"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, _, value = raw.partition("=")
            if key.strip() != "APP_BASE_URL":
                continue
            parsed = urlparse(value.strip())
            if parsed.hostname:
                hosts.add(parsed.hostname.lower())
    for part in os.getenv("BLACKDARK_HTTP_HOST_ALLOWLIST", "").split(","):
        host = part.strip().lower()
        if host:
            hosts.add(host)
    for default in (
        "blackdark-production.up.railway.app",
        "blackdark.io",
        "www.blackdark.io",
        "localhost",
        "127.0.0.1",
    ):
        hosts.add(default)
    return hosts


def _ensure_host_allowlist(base_url: str) -> None:
    hosts = _load_launch_env_hosts()
    parsed = urlparse(base_url)
    if parsed.hostname:
        hosts.add(parsed.hostname.lower())
    os.environ["BLACKDARK_HTTP_HOST_ALLOWLIST"] = ",".join(sorted(hosts))


def probe(
    url: str,
    label: str,
    *,
    ok_status: frozenset[int] = frozenset({200}),
    timeout: float = _DEFAULT_PROBE_TIMEOUT,
) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        safe_url = assert_safe_http_url(url)
        with safe_urlopen(safe_url, timeout=timeout) as resp:
            ok = resp.status in ok_status
    except urllib.error.HTTPError as exc:
        ok = exc.code in ok_status
    except (OSError, ValueError, TimeoutError):
        ok = False
    ms = (time.perf_counter() - t0) * 1000
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: {ms:.0f}ms — {url}")
    return ok, ms


def _probe_group(
    items: list[tuple[str, str, frozenset[int] | None]],
    *,
    timeout: float = _DEFAULT_PROBE_TIMEOUT,
) -> int:
    ok_count = 0
    for url, label, ok_status in items:
        codes = ok_status if ok_status is not None else frozenset({200})
        ok, _ = probe(url, label, ok_status=codes, timeout=timeout)
        if ok:
            ok_count += 1
    return ok_count


def _probe_admin_gates(base: str) -> None:
    for path in ("/admin", "/admin/launch", "/admin/plan", "/admin/roadmap"):
        try:
            with safe_urlopen(assert_safe_http_url(f"{base}{path}"), timeout=12) as resp:
                print(f"  [WARN] {path} publicly reachable — got {resp.status}")
        except ValueError as exc:
            print(f"  [FAIL] {path} blocked by URL allowlist: {exc}")
        except TimeoutError:
            print(f"  [WARN] {path} → timeout (treat as slow gate)")
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                print(f"  [OK] {path} gated/missing as expected ({exc.code})")
            else:
                print(f"  [WARN] {path} → HTTP {exc.code}")


def _probe_launch57(base: str) -> int:
    items = [
        (f"{base}/api/launch57/guest-trust", "launch57_guest_trust", frozenset({200})),
        (f"{base}/api/launch57/command-home", "launch57_command_home_anon", frozenset({401})),
        (f"{base}/oracle/BTC/quick", "oracle_quick", frozenset({200})),
        (f"{base}/api/launch/readiness", "launch_readiness", frozenset({200})),
        (f"{base}/api/production/guard", "production_guard", frozenset({200})),
    ]
    return _probe_group(items)


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
    base = assert_safe_http_url(sys.argv[1] if len(sys.argv) > 1 else "[REDACTED]")
    _ensure_host_allowlist(base)

    print(f"BLACKDARK LAUNCH VERIFY | {base}\n")

    pages = [
        (f"{base}/", "landing", None),
        (f"{base}/dashboard", "dashboard", frozenset({200, 401})),
        (f"{base}/platform", "platform", None),
        (f"{base}/login", "login", None),
        (f"{base}/terms", "terms", None),
        (f"{base}/manifest.json", "pwa manifest", None),
    ]
    apis = [
        (f"{base}/health/live", "liveness", None),
        (f"{base}/health/ready", "readiness", None),
        (f"{base}/api/services/status", "services", frozenset({200, 503})),
        # Some Railway builds omit the billing router; launch/readiness exposes billing_configured.
        (f"{base}/api/billing/status", "billing", frozenset({200})),
        (f"{base}/api/arbitrage/opportunities", "arbitrage", frozenset({200, 401, 503})),
    ]
    total = len(pages) + len(apis)
    ok_count = _probe_group(pages + apis)

    print("\nLaunch-57 live slice:")
    launch57_ok = _probe_launch57(base)
    launch57_total = 5
    ok_count += launch57_ok
    total += launch57_total

    # Admin launch page is gated (403 without admin) — must NOT be a public 200
    _probe_admin_gates(base)

    # Constitution product probes
    constitution_apis = [
        (f"{base}/oracle/BTC?ux_mode=beginner&lang=en", "oracle_beginner_en", frozenset({200, 403})),
        (f"{base}/api/oracle/accuracy/public", "public_accuracy", None),
        (f"{base}/api/oracle/net-edge-truth", "net_edge_truth", None),
        (f"{base}/api/oracle/half-life", "half_life", None),
        (f"{base}/api/due-diligence/evidence-pack/public-summary", "evidence_public", None),
        (f"{base}/oracle-accuracy", "accuracy_page", None),
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
