"""GTM, launch readiness, and platform stats API."""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(tags=["gtm"])


@router.get("/api/platform/stats")
async def platform_stats():
    from billing_service import billing_configured
    from database import count_telegram_free_subscribers, fetch_platform_user_stats

    stats = await fetch_platform_user_stats()
    stats["billing_configured"] = billing_configured()
    stats["stripe_configured"] = billing_configured()
    stats["telegram_configured"] = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    stats["telegram_free_subscribers"] = await count_telegram_free_subscribers()
    return stats


@router.get("/api/gtm/status")
async def gtm_status():
    from gtm_service import fetch_gtm_status

    return await fetch_gtm_status()


@router.get("/api/launch/readiness")
async def launch_readiness():
    from billing_service import billing_configured
    from gtm_service import fetch_gtm_status
    from production_guard import evaluate_production_guard
    from uptime_monitor import uptime_stats

    uptime = uptime_stats(window_hours=24)
    probes = int(uptime.get("probes_total") or 0)
    gtm = await fetch_gtm_status()
    guard = evaluate_production_guard()
    return {
        "production_url": os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app"),
        "billing_configured": billing_configured(),
        "stripe_configured": billing_configured(),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "uptime_probes_24h": probes,
        "uptime_meets_dd_gate": probes >= 10,
        "uptime_external_monitor": "https://uptimerobot.com -> /health/live every 5 min",
        "production_guard": guard,
        "gtm_status": "/api/gtm/status",
        "architecture_dd": "/api/due-diligence/architecture",
        "setup_scripts": {
            "launch": "python scripts/setup_production_launch.py",
            "stripe": "python scripts/setup_stripe_production.py",
            "telegram": "python scripts/setup_telegram_production.py",
        },
        "ninety_day_targets": gtm.get("ninety_day_targets"),
        "blockers": list(gtm.get("blockers") or []) + list(guard.get("required_failures") or []),
        "dd_technical_report": "/api/due-diligence/technical",
        "next_steps": gtm.get("next_actions")
        or [
            "Configure UptimeRobot on /health/live",
            "Set LEMON_SQUEEZY_CHECKOUT_PRO or Stripe keys in Railway",
            "Set DATABASE_URL Postgres + SERVICE_MODE=web",
            "Share landing page — target 10 paid users",
        ],
    }


@router.get("/api/production/guard")
async def production_guard_api():
    from production_guard import evaluate_production_guard

    return evaluate_production_guard()
