#!/usr/bin/env python3
"""Production launch setup - env checklist + UptimeRobot instructions."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD_URL = os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app").rstrip("/")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _probe(url: str) -> tuple[bool, int | None]:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status == 200, resp.status
    except Exception:
        return False, None


def main() -> int:
    print("=" * 60)
    print("BLACKDARK - Production Launch Setup")
    print("=" * 60)
    print(f"\nProduction URL: {PROD_URL}\n")

    # Live probes
    live_ok, live_code = _probe(f"{PROD_URL}/health/live")
    oracle_ok, oracle_code = _probe(f"{PROD_URL}/oracle/BTC")
    print(f"  [{'OK' if live_ok else 'FAIL'}] /health/live  HTTP {live_code}")
    print(f"  [{'OK' if oracle_ok else 'FAIL'}] /oracle/BTC    HTTP {oracle_code}")

    try:
        with urllib.request.urlopen(f"{PROD_URL}/api/build-info", timeout=15) as resp:
            info = json.loads(resp.read().decode())
        print(f"  Build: {info.get('release')} ({str(info.get('git_commit') or '')[:8]})")
    except Exception:
        print("  Build: (could not fetch /api/build-info)")

    print("\n--- Railway Variables (set in dashboard) ---")
    checks = [
        ("SERVICE_MODE", "web - Oracle-only lightweight process"),
        ("DATABASE_URL", "postgresql://... - Railway Postgres plugin"),
        ("LEMON_SQUEEZY_CHECKOUT_PRO", "Lemon Squeezy checkout URL (Egypt-friendly)"),
        ("REDIS_URL", "Railway Redis or Upstash (recommended)"),
        ("SERVICE_BUS_LOCAL", "false when REDIS_URL set"),
        ("SENTRY_DSN", "sentry.io error tracking (recommended)"),
        ("SECRETS_MASTER_KEY", "32-byte hex - required for vault"),
        ("SESSION_TOKEN_PEPPER", "random string - session security"),
        ("TELEGRAM_BOT_TOKEN", "from @BotFather"),
        ("TELEGRAM_WEBHOOK_URL", f"{PROD_URL}/api/telegram/webhook"),
        ("APP_BASE_URL", PROD_URL),
        ("PRICE_FEED_WS_ONLY", "false (Railway cloud)"),
        ("UPTIME_SELF_PROBE_ENABLED", "true"),
    ]
    missing = 0
    for key, hint in checks:
        val = _env(key)
        ok = bool(val)
        required = key in {"SERVICE_MODE", "DATABASE_URL", "LEMON_SQUEEZY_CHECKOUT_PRO", "APP_BASE_URL"}
        if not ok and required:
            missing += 1
        mark = "SET" if ok else "MISSING"
        print(f"  [{mark}] {key}")
        if not ok:
            print(f"         -> {hint}")

    try:
        from production_guard import evaluate_production_guard

        guard = evaluate_production_guard()
        print("\n--- Production Guard ---")
        print(f"  Required pass: {guard.get('required_pass')}")
        if guard.get("required_failures"):
            print(f"  Failures: {', '.join(guard['required_failures'])}")
        print(f"  API: {PROD_URL}/api/production/guard")
    except Exception:
        pass

    print("\n--- GTM setup scripts ---")
    print("  python scripts/railway_production_checklist.py")
    print(f"  Live tracker: {PROD_URL}/api/gtm/status")

    print("\n--- UptimeRobot (DD #1 - do this today) ---")
    print("  1. Go to https://uptimerobot.com (free account)")
    print("  2. Add Monitor -> HTTP(s)")
    print(f"  3. URL: {PROD_URL}/health/live")
    print("  4. Interval: 5 minutes")
    print("  5. Save -> after 24h re-check /api/due-diligence/technical")
    print("\n  Template: config/uptime_monitor.example.json")

    print("\n--- Next metrics (90-day LOI) ---")
    print("  - 50+ live oracle labels")
    print("  - 10+ paid subscribers (Stripe live)")
    print("  - 1,000+ behavior events / 90 days")
    print("  - 1 trained .joblib model")

    print(f"\nMissing env vars locally: {missing} (Railway may have them set)")
    print("=" * 60)
    return 0 if live_ok and oracle_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
