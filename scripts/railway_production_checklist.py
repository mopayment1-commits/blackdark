#!/usr/bin/env python3
"""Print Railway production variables checklist (copy-paste into Railway dashboard)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PROD_URL = os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app").rstrip("/")

REQUIRED = [
    ("SERVICE_MODE", "web"),
    ("ENV", "production"),
    ("APP_BASE_URL", PROD_URL),
    ("DATABASE_URL", "<Railway Postgres plugin URL>"),
    ("LEMON_SQUEEZY_CHECKOUT_PRO", "https://blackdark.lemonsqueezy.com/checkout/buy/d044fb7a-5722-498a-885b-dfd04fb7ed05"),
    ("PRICE_FEED_WS_ONLY", "false"),
    ("UPTIME_SELF_PROBE_ENABLED", "true"),
]

RECOMMENDED = [
    ("REDIS_URL", "<Railway Redis or Upstash URL>"),
    ("SERVICE_BUS_LOCAL", "false"),
    ("SENTRY_DSN", "<sentry.io project DSN>"),
    ("TELEGRAM_BOT_TOKEN", "<from @BotFather>"),
    ("TELEGRAM_WEBHOOK_URL", f"{PROD_URL}/api/telegram/webhook"),
    ("SECRETS_MASTER_KEY", "<openssl rand -hex 32>"),
    ("SESSION_TOKEN_PEPPER", "<openssl rand -hex 16>"),
]


def main() -> int:
    print("=" * 60)
    print("BLACKDARK - Railway Variables Checklist")
    print("=" * 60)
    print("\nREQUIRED (paste into Railway -> Variables):\n")
    for key, val in REQUIRED:
        print(f"  {key}={val}")

    print("\nRECOMMENDED:\n")
    for key, val in RECOMMENDED:
        print(f"  {key}={val}")

    print("\nReplicas: set to 2 in Railway Settings -> Deploy")
    print(f"UptimeRobot URL: {PROD_URL}/health/live")
    print(f"Verify after deploy: {PROD_URL}/api/production/guard")
    print(f"Architecture DD: {PROD_URL}/api/due-diligence/architecture")

    try:
        from production_guard import evaluate_production_guard

        report = evaluate_production_guard()
        print("\nLocal guard preview:")
        print(json.dumps({
            "ready": report.get("ready") if isinstance(report, dict) else None,
            "soft_launch": report.get("soft_launch") if isinstance(report, dict) else None,
            "required_failures": report.get("required_failures") if isinstance(report, dict) else None,
            "viral_ha_enforced": report.get("viral_ha_enforced") if isinstance(report, dict) else None,
        }, indent=2))
    except Exception as exc:
        print(f"\n(local preview skipped: {exc})")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
