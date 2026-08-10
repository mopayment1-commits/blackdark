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
    from billing_service import billing_configured, billing_provider
    from gtm_service import fetch_gtm_status
    from launch_checklist import launch_checklist
    from production_guard import evaluate_production_guard
    from uptime_monitor import uptime_stats

    uptime = uptime_stats(window_hours=24)
    probes = int(uptime.get("probes_total") or 0)
    gtm = await fetch_gtm_status()
    guard = evaluate_production_guard()
    checklist = launch_checklist()
    constitution_modules = all(
        __import__("pathlib").Path(p).exists()
        for p in (
            "docs/PRODUCT_CONSTITUTION_AR.md",
            "decision_enrichment.py",
            "net_edge_truth.py",
            "persona_clarity.py",
            "signal_registry.py",
            "acquirer_evidence_pack.py",
            "ux_mode.py",
        )
    )
    return {
        "production_url": os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app"),
        "billing_configured": billing_configured(),
        "billing_provider": billing_provider(),
        "stripe_configured": billing_configured(),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "uptime_probes_24h": probes,
        "uptime_meets_dd_gate": probes >= 10,
        "uptime_external_monitor": "https://uptimerobot.com -> /health/live every 5 min",
        "production_guard": guard,
        "launch_checklist": {
            "percent": checklist.get("launch_percent"),
            "ready": checklist.get("launch_ready"),
            "blocked_count": checklist.get("blocked_count"),
            "blocked_ids": [r["id"] for r in checklist.get("items", []) if r.get("status") == "blocked"],
        },
        "constitution": {
            "ref": "docs/PRODUCT_CONSTITUTION_AR.md",
            "modules_ready": constitution_modules,
            "primary_oracle": "/oracle/BTC?ux_mode=beginner&lang=en",
            "accuracy_page": "/oracle-accuracy",
            "evidence_public": "/api/due-diligence/evidence-pack/public-summary",
            "evidence_full": "/api/due-diligence/evidence-pack",
        },
        "gtm_status": "/api/gtm/status",
        "architecture_dd": "/api/due-diligence/architecture",
        "setup_scripts": {
            "finalize": "python scripts/finalize_launch.py",
            "secrets": "python scripts/generate_launch_secrets.py --write",
            "launch": "python scripts/setup_production_launch.py",
            "stripe": "python scripts/setup_stripe_production.py",
            "telegram": "python scripts/setup_telegram_production.py",
        },
        "ninety_day_targets": gtm.get("ninety_day_targets"),
        "blockers": list(gtm.get("blockers") or []) + list(guard.get("required_failures") or []),
        "dd_technical_report": "/api/due-diligence/technical",
        "code_launch_ready": constitution_modules and checklist.get("blocked_count", 99) <= 2,
        "quality_honesty": {
            "api": "/api/public/quality-honesty-closure",
            "doc": "docs/QUALITY_HONESTY_SOFT_LAUNCH_AR.md",
            "soft_launch_honesty_complete": True,
            "world_class_100_complete": False,
            "claim_boundary": (
                "Code Soft Launch readiness ≠ viral HA proven ≠ live beta ops complete. "
                "HUMAN_OPS (domain/PSP/OAuth) remain outside this flag."
            ),
        },
        "next_steps": [
            "python scripts/finalize_launch.py",
            "Paste .env.launch.local into Railway Variables",
            "python scripts/setup_payments_usd.py — Lemon Pro/Whale USD + webhook (or Stripe)",
            "Verify /api/billing/payments launch_ready=true",
            "Verify /api/production/guard → required_pass=true",
            "UptimeRobot on /health/live → announce",
            "Confirm /api/public/quality-honesty-closure → world_class_100_complete=false",
        ],
    }


@router.get("/api/production/guard")
async def production_guard_api():
    from production_guard import evaluate_production_guard

    return evaluate_production_guard()

@router.get("/api/pricing")
async def api_pricing():
    """Trust OS depth ladder — Proof Pass / Decision Pro / Decision Desk / Institutional."""
    from pricing_catalog import pricing_catalog

    return pricing_catalog()

