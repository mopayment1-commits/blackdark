"""
BLACKDARK — Go-to-market status (MKT-001 … MKT-006 launch tracker).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

MKT_DOCS = {
    "icp": ROOT / "docs" / "MKT_ICP.md",
    "competitive_matrix": ROOT / "docs" / "MKT_COMPETITIVE_MATRIX.md",
    "market_barriers": ROOT / "docs" / "MKT_MARKET_BARRIERS.md",
}

NINETY_DAY_TARGETS = {
    "paid_subscribers": 10,
    "oracle_labels": 50,
    "behavior_events": 1000,
    "telegram_free_subscribers": 25,
}


def _doc_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 200


def _stripe_ready() -> dict[str, Any]:
    from billing_service import billing_configured, billing_provider, lemon_squeezy_checkout_url, stripe_configured

    keys = {
        "secret": bool(os.getenv("STRIPE_SECRET_KEY", "").strip()),
        "webhook": bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()),
        "price_pro": bool(os.getenv("STRIPE_PRICE_PRO", "").strip()),
        "success_url": bool(os.getenv("STRIPE_SUCCESS_URL", "").strip()),
    }
    ls_pro = lemon_squeezy_checkout_url("pro")
    return {
        "configured": billing_configured(),
        "provider": billing_provider(),
        "keys": keys,
        "lemon_squeezy_pro_url": bool(ls_pro),
        "checkout_url": ls_pro or "/create-checkout-session?tier=pro",
        "setup_script": "python scripts/setup_stripe_production.py",
    }


def _telegram_ready() -> dict[str, Any]:
    token = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    webhook = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()
    polling = os.getenv("TELEGRAM_POLLING_ENABLED", "").strip().lower() in {"1", "true", "yes"}
    mode = "webhook" if webhook else ("polling" if polling or token else "none")
    if token and not webhook and not polling:
        mode = "polling_auto"
    return {
        "bot_configured": token,
        "mode": mode,
        "webhook_url": webhook or None,
        "bot_username": os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@") or None,
        "free_alerts_enabled": os.getenv("TELEGRAM_FREE_ALERTS_ENABLED", "true").lower()
        in {"1", "true", "yes"},
        "setup_script": "python scripts/setup_telegram_production.py",
    }


def _mkt_verdicts(metrics: dict[str, Any], docs: dict[str, bool]) -> dict[str, str]:
    paid = int(metrics.get("paid_subscribers") or 0)
    trials = int(metrics.get("active_trials") or 0)
    telegram_subs = int(metrics.get("telegram_free_subscribers") or 0)

    demand = "pass" if paid >= 3 else ("partial" if paid >= 1 or trials >= 5 else "fail")
    positioning = "pass" if docs.get("icp") and docs.get("competitive_matrix") else "partial"
    barriers = "pass" if docs.get("market_barriers") else "partial"

    return {
        "MKT-001_target_market": "partial" if docs.get("icp") else "fail",
        "MKT-002_market_size": "pass",
        "MKT-003_competitors": "pass" if docs.get("competitive_matrix") else "partial",
        "MKT-004_positioning": positioning,
        "MKT-005_barriers": barriers,
        "MKT-006_customer_demand": demand,
        "overall": "partial" if paid >= 1 or telegram_subs >= 10 else "fail",
    }


async def fetch_gtm_status() -> dict[str, Any]:
    from database import (
        count_telegram_free_subscribers,
        fetch_behavior_event_stats,
        fetch_platform_user_stats,
        db_count_waitlist,
    )

    users = await fetch_platform_user_stats()
    behavior = await fetch_behavior_event_stats(days=90)
    telegram_subs = await count_telegram_free_subscribers()
    waitlist = await db_count_waitlist()

    labeled = 0
    try:
        from database import fetch_oracle_audit_stats

        acc = await fetch_oracle_audit_stats(limit=1, include_synthetic=False)
        live = (acc or {}).get("live") or {}
        labeled = int(live.get("resolved_predictions") or 0)
    except Exception:
        pass

    metrics = {
        **users,
        "waitlist_signups": waitlist,
        "telegram_free_subscribers": telegram_subs,
        "behavior_events_90d": int(behavior.get("total_events") or 0),
        "oracle_labels_resolved": labeled,
    }

    docs = {key: _doc_ready(path) for key, path in MKT_DOCS.items()}
    targets = {
        key: {
            "current": metrics.get(
                {
                    "paid_subscribers": "paid_subscribers",
                    "oracle_labels": "oracle_labels_resolved",
                    "behavior_events": "behavior_events_90d",
                    "telegram_free_subscribers": "telegram_free_subscribers",
                }[key],
                0,
            ),
            "target": goal,
            "met": int(metrics.get(
                {
                    "paid_subscribers": "paid_subscribers",
                    "oracle_labels": "oracle_labels_resolved",
                    "behavior_events": "behavior_events_90d",
                    "telegram_free_subscribers": "telegram_free_subscribers",
                }[key],
                0,
            ))
            >= goal,
        }
        for key, goal in NINETY_DAY_TARGETS.items()
    }

    stripe = _stripe_ready()
    telegram = _telegram_ready()
    blockers: list[str] = []
    if not stripe["configured"]:
        blockers.append("Set Stripe live keys (STRIPE_SECRET_KEY, STRIPE_PRICE_PRO, STRIPE_WEBHOOK_SECRET)")
    if not telegram["bot_configured"]:
        blockers.append("Set TELEGRAM_BOT_TOKEN and run scripts/setup_telegram_production.py")
    if int(metrics.get("paid_subscribers") or 0) < 1:
        blockers.append("Get first paid Pro subscriber via /create-checkout-session?tier=pro")

    return {
        "production_url": os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app"),
        "stripe": stripe,
        "telegram": telegram,
        "marketing_docs": {**docs, "paths": {k: str(v.relative_to(ROOT)) for k, v in MKT_DOCS.items()}},
        "metrics": metrics,
        "ninety_day_targets": targets,
        "mkt_verdicts": _mkt_verdicts(metrics, docs),
        "blockers": blockers,
        "next_actions": [
            "Share landing + Oracle demo on X/Telegram crypto groups",
            "Enable Stripe live checkout — test $29 Pro trial end-to-end",
            "Message @BotFather bot link on landing — target 25 free Telegram subs",
            "Track progress: GET /api/gtm/status",
        ],
    }
