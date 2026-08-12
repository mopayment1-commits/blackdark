#!/usr/bin/env python3
"""Print Railway production variables checklist (placeholders only — no live secrets)."""
from __future__ import annotations

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
    ("LEMON_SQUEEZY_CHECKOUT_PRO", "https://blackdark.lemonsqueezy.com/checkout/buy/<checkout-id>"),
    ("PRICE_FEED_WS_ONLY", "false"),
    ("UPTIME_SELF_PROBE_ENABLED", "true"),
]

RECOMMENDED = [
    ("REDIS_URL", "<Railway Redis or Upstash URL>"),
    ("SERVICE_BUS_LOCAL", "false"),
    ("SENTRY_DSN", "<sentry.io project DSN>"),
    ("TELEGRAM_BOT_TOKEN", "<from @BotFather — do not paste into logs>"),
    ("TELEGRAM_WEBHOOK_URL", f"{PROD_URL}/api/telegram/webhook"),
    ("SECRETS_MASTER_KEY", "<openssl rand -hex 32 — keep private>"),
    ("SESSION_TOKEN_PEPPER", "<openssl rand -hex 16 — keep private>"),
    ("ADMIN_API_KEY", "<openssl rand -hex 24 — or ADMIN_API_KEY_FILE>"),
]


def main() -> int:
    print("=" * 60)
    print("BLACKDARK - Railway Variables Checklist")
    print("=" * 60)
    print("\nREQUIRED (paste into Railway -> Variables):\n")
    for key, val in REQUIRED:
        # Placeholder strings only — never live env values.
        print(f"  {key}={val}")

    print("\nRECOMMENDED:\n")
    for key, val in RECOMMENDED:
        print(f"  {key}={val}")

    print("\nReplicas: set to 2 in Railway Settings -> Deploy")
    print(f"UptimeRobot URL: {PROD_URL}/health/live")
    print(f"Verify after deploy: {PROD_URL}/api/production/guard")
    print(f"Architecture DD: {PROD_URL}/api/due-diligence/architecture")

    try:
        from production_guard import public_guard_console_summary

        summary = public_guard_console_summary()
        print("\nLocal guard preview (statuses only — no secrets):")
        print(f"  required_pass={summary['required_pass']}")
        print(f"  soft_launch={summary['soft_launch']}")
        print(f"  database={summary['database']}")
        print(f"  required_failure_count={summary['required_failure_count']}")
        for code in summary["required_failure_ids"]:
            print(f"  failure_code={code}")
        for code in summary["warning_ids"]:
            print(f"  warning_code={code}")
    except Exception:
        print("\n(local preview skipped)")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
