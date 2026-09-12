#!/usr/bin/env python3
"""Validate post-deploy monitoring configuration (uptime + alerts + rate limits)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    checks: list[dict] = []
    ok = True

    def add(name: str, passed: bool, hint: str) -> None:
        nonlocal ok
        if not passed:
            ok = False
        checks.append({"check": name, "ok": passed, "hint": hint})

    mon_enabled = os.getenv("MONITORING_ENABLED", "true").lower() in {"1", "true", "yes"}
    add("monitoring_enabled", mon_enabled, "Set MONITORING_ENABLED=true")

    base = os.getenv("MONITORING_BASE_URL") or os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL")
    add("monitoring_base_url", bool(base), "Set MONITORING_BASE_URL or APP_BASE_URL to public deploy URL")

    telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN") and (os.getenv("OPS_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")))
    add("ops_telegram", telegram, "Set TELEGRAM_BOT_TOKEN + OPS_TELEGRAM_CHAT_ID for instant alerts")

    webhook = bool(os.getenv("MONITORING_WEBHOOK_URL"))
    add("monitoring_webhook", webhook or telegram, "Set MONITORING_WEBHOOK_URL (PagerDuty/Slack) or Telegram")

    uptime = os.getenv("UPTIME_SELF_PROBE_ENABLED", "true").lower() in {"1", "true", "yes"}
    add("uptime_self_probe", uptime, "UPTIME_SELF_PROBE_ENABLED=true (default)")

    # Recommended but not blocking — logged as warnings
    warnings: list[str] = []
    if not os.getenv("SENTRY_DSN"):
        warnings.append("SENTRY_DSN not set — recommended for production error tracking")
    if not (os.getenv("EXTERNAL_UPTIME_MONITOR_URL") or os.getenv("UPTIMEROBOT_MONITOR_URL")):
        warnings.append("External uptime monitor not configured — set UptimeRobot on /health/live")

    report = {
        "monitoring_setup_ok": ok,
        "checks": checks,
        "next_steps": [
            "1. Set MONITORING_BASE_URL=https://your-deploy-url",
            "2. Set OPS_TELEGRAM_CHAT_ID + TELEGRAM_BOT_TOKEN",
            "3. Optional: MONITORING_WEBHOOK_URL for PagerDuty/Slack",
            "4. External: UptimeRobot monitor on /health/live every 60s",
            "5. Run: python3 scripts/free_api_rate_limit_audit.py",
            "6. Verify: curl $MONITORING_BASE_URL/api/monitoring/status",
        ],
    }
    out = ROOT / "MONITORING_SETUP_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
