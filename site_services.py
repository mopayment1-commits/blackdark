"""
BLACKDARK — Companion site services catalog (trust rail around Trust OS).

Footer, Follow us, Contact, FAQ, How it works, About, Status, Changelog, Feedback.
Share stays Proof-Card-centric; Follow is brand presence — never mixed in the hero.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_FEEDBACK_LOCK = threading.Lock()
_FEEDBACK_PATH = Path("data/feedback.jsonl")


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def telegram_alerts_bot_url() -> str:
    """Notification bot — Join Telegram Alerts CTA."""
    return _env("BRAND_TELEGRAM_ALERTS_BOT", "https://t.me/BLACKDARKAI_oncall_bot")


def telegram_community_urls() -> dict[str, str]:
    """Telegram bot, group, and channel (env overrides)."""
    return {
        "bot": telegram_alerts_bot_url(),
        "chat_group": _env(
            "BRAND_TELEGRAM_CHAT_GROUP",
            "https://t.me/+klz-XoXG6BI1OTE8",
        ),
        "channel": _env("BRAND_SOCIAL_TELEGRAM_CHANNEL", "https://t.me/BLACKDARKAPP"),
    }


def brand_social() -> list[dict[str, str]]:
    """Official brand profiles (Follow us) — configure via env."""
    tg = telegram_community_urls()
    items = [
        {
            "id": "x",
            "label": "X",
            "href": _env("BRAND_SOCIAL_X", "https://x.com/BLACKDARKio"),
        },
        {
            "id": "reddit",
            "label": "Reddit",
            "href": _env(
                "BRAND_SOCIAL_REDDIT",
                "https://www.reddit.com/user/Mopayment",
            ),
        },
        {
            "id": "facebook",
            "label": "Facebook",
            "href": _env(
                "BRAND_SOCIAL_FACEBOOK",
                "https://www.facebook.com/share/19vLBQzveA/?mibextid=wwXIfr",
            ),
        },
        {
            "id": "telegram",
            "label": "Telegram",
            "href": _env("BRAND_SOCIAL_TELEGRAM", tg["channel"]),
        },
        {
            "id": "linkedin",
            "label": "LinkedIn",
            "href": _env(
                "BRAND_SOCIAL_LINKEDIN",
                "https://www.linkedin.com/in/blackdarkio",
            ),
        },
    ]
    return [i for i in items if i["href"]]


def contact_channels() -> dict[str, Any]:
    from commercial_support import commercial_support_config

    cfg = commercial_support_config()
    support = cfg["support_email"]
    urgent = cfg["urgent_escalation"]
    complaints = _env("COMPLAINTS_EMAIL", support)
    sales = _env("SALES_EMAIL", support)
    wa = _env("WHATSAPP_BUSINESS_E164", "")  # e.g. 15551234567
    phone_inst = _env("INSTITUTIONAL_PHONE", "")  # Room only — optional
    wa_url = f"https://wa.me/{wa}" if wa else ""
    return {
        "support_email": support,
        "support_owner": cfg["support_owner"],
        "support_hours": cfg["support_hours"],
        "urgent_escalation": urgent,
        "complaints_email": complaints,
        "sales_email": sales,
        "whatsapp_business_e164": wa or None,
        "whatsapp_url": wa_url or None,
        "institutional_phone": phone_inst or None,
        "sla_note": (
            f"Support hours: {cfg['support_hours']}. "
            f"Urgent: email {support} with subject prefix {urgent['subject_prefix']}."
        ),
        "never_ask": ["card_number", "cvv", "full_password_in_email"],
        "feedback_path": "/feedback",
    }


FAQ_ITEMS: list[dict[str, str]] = [
    {
        "q": "Is BLACKDARK financial advice?",
        "a": "No. Outputs are decision intelligence for research only. You verify on the Public Accuracy Ledger and remain responsible for your actions.",
    },
    {
        "q": "Do you guarantee accuracy or profits?",
        "a": "No. We sell reviewable decisions and proof — not guaranteed returns. Hits and misses are published on the Ledger.",
    },
    {
        "q": "What is Free ($0)?",
        "a": "Trust Pulse, Public Accuracy Ledger, one Oracle decision (BTC/ETH), one decision certificate, and saved language — on-device where applicable.",
    },
    {
        "q": "What do I get with Beginner ($9.99/mo)?",
        "a": "Everything in Free plus Watchlist (5 symbols), one decision alert, decision log (20), compare two assets, and offline last-known decisions.",
    },
    {
        "q": "What is Pro ($29/mo)?",
        "a": "Everything in Beginner plus 20-symbol Watchlist, unlimited alerts, full decision log, compare five assets, charts, share decision, and dark/light theme.",
    },
    {
        "q": "What is Desk ($79/mo)?",
        "a": "Everything in Pro plus all symbols on Watchlist, advanced alerts, read API, certificate export, and priority support.",
    },
    {
        "q": "How do funds engage (Institution)?",
        "a": "Full API, custom reports, SLA, and extended historical data. Talk to us — not self-serve checkout.",
    },
    {
        "q": "What can I share on social / WhatsApp?",
        "a": "Share Proof Cards and Ledger snapshots (decision + short why + verify link). Do not share API keys or private holdings.",
    },
    {
        "q": "Where is AI Chat and who can use it?",
        "a": "Inside the dashboard Operate/Desk experience. Available on DECIDE / PRO and paid tiers above. It explains the current decision context — it does not replace the Oracle or guarantee outcomes.",
    },
    {
        "q": "How do I reset my password?",
        "a": "Use Forgot password on the Login page. We email a one-time link (SMTP or queued outbox).",
    },
    {
        "q": "How do refunds work?",
        "a": "See /refund. Self-serve plans are USD monthly; trials convert unless cancelled. Refunds follow the refund policy and applicable law.",
    },
    {
        "q": "How do I contact support or WhatsApp?",
        "a": "Use /contact for email channels. WhatsApp Business appears when WHATSAPP_BUSINESS_E164 is configured. Phone is institutional/optional only.",
    },
    {
        "q": "Where do I send product suggestions?",
        "a": "Use /feedback — suggestions are stored and emailed to support. Never include card numbers or passwords.",
    },
]

HOW_IT_WORKS_STEPS: list[dict[str, str]] = [
    {
        "id": "decide",
        "title": "Decide",
        "body": "Ask the Oracle for one clear Act / Wait with a human Why (Top factors).",
    },
    {
        "id": "prove",
        "title": "Prove",
        "body": "Export a Decision Certificate — shareable Proof Card with verify link.",
    },
    {
        "id": "verify",
        "title": "Verify",
        "body": "Check the Public Accuracy Ledger — hits and misses, publicly.",
    },
]

CHANGELOG: list[dict[str, str]] = [
    {
        "date": "2026-08-08",
        "title": "Trust OS Design System v1",
        "body": "Syne + IBM Plex, cyan trust palette, three intentional motions, hero budget, no ARENA/FOMO/Inter/purple defaults.",
    },
    {
        "date": "2026-08-08",
        "title": "Trust Pulse",
        "body": "First-open live Act/Wait + Why + Ledger proof + SSE freshness — not a news digest.",
    },
    {
        "date": "2026-08-08",
        "title": "Companion trust rail",
        "body": "Unified footer, Follow us, FAQ, How it works, About, Status, Feedback, Legal hub, Operate AI Chat panel.",
    },
    {
        "date": "2026-08-08",
        "title": "Trust OS lenses",
        "body": "Prove → Operate → Desk → Room navigation with Decide / Verify / My book / Alerts.",
    },
    {
        "date": "2026-08-08",
        "title": "Identity & USD payments",
        "body": "Auth recovery, profile/avatars, USD hosted checkout posture (PCI SAQ A).",
    },
]


def footer_manifest() -> dict[str, Any]:
    contact = contact_channels()
    return {
        "brand": "BLACKDARK",
        "tagline": "Trust OS — Decide. Prove it. Share it.",
        "story": "Prove → Operate → Desk → Room",
        "product": [
            {"label": "Oracle", "href": "/#oracle"},
            {"label": "Dashboard", "href": "/dashboard"},
            {"label": "Pricing", "href": "/pricing"},
        ],
        "trust": [
            {"label": "Public Accuracy Ledger", "href": "/oracle-accuracy"},
            {"label": "Discipline Mirror", "href": "/discipline-mirror"},
        ],
        "company": [
            {"label": "Contact", "href": "/contact"},
            {"label": "About", "href": "/about"},
        ],
        "legal": [
            {"label": "Disclaimer", "href": "/disclaimer"},
            {"label": "Terms", "href": "/terms"},
            {"label": "Privacy", "href": "/privacy"},
        ],
        "follow": brand_social(),
        "telegram_alerts_url": telegram_alerts_bot_url(),
        "telegram_community": telegram_community_urls(),
        "contact": contact,
        "disclaimer_line": "Four-layer legal shield active. Not financial advice. AI cannot guarantee returns. Verify on the Public Accuracy Ledger.",
    }


def site_services_manifest() -> dict[str, Any]:
    return {
        "product": "BLACKDARK Trust OS",
        "footer": footer_manifest(),
        "faq": FAQ_ITEMS,
        "how_it_works": HOW_IT_WORKS_STEPS,
        "changelog": CHANGELOG,
        "about": about_blurb(),
        "ai_chat": {
            "surface": "/dashboard?lens=operate#ai-chat",
            "tiers": ["pro", "whale"],
            "role": "Explains current decision context — does not replace Oracle",
            "free_tier": False,
        },
        "share_policy": {
            "allowed": ["proof_card", "ledger_snapshot"],
            "channels": ["x", "whatsapp", "telegram", "copy", "native_share"],
            "forbidden": ["api_keys", "raw_holdings_without_consent", "card_data"],
        },
        "binding_doc": "docs/SITE_COMPANION_SERVICES.md",
    }


def about_blurb() -> dict[str, Any]:
    capabilities = [
        "Single-sentence Oracle decisions with live freshness and factor breakdown",
        "Public Accuracy Ledger with hash-chained proof of hits and misses",
        "Trust Pulse for real-time Act/Wait signals under five seconds",
        "Sealed Prediction Markets with timed certificates and public resolution",
        "Verified Miss Bounty for reported model errors with subscription credit",
        "Arb Opportunities for cross-venue price discrepancies (paid users)",
        "Discipline Mirror for private follow-vs-override tracking",
        "Decision Certificates with shareable proof",
        "Glass Box Challenge for public verification",
        "Multi-language support across 25 languages",
        "Institutional-grade data provenance and audit trail",
    ]
    return {
        "title": "About BlackDark",
        "lead": (
            "Institutional-grade market intelligence built for clarity, not noise — "
            "one clear Act or Wait decision backed by transparent evidence."
        ),
        "capabilities": capabilities,
        "disclaimer": (
            "BlackDark is an analytical research tool. It is not financial advice. "
            "All outcomes, including misses, are published on the Public Accuracy Ledger "
            "for independent verification."
        ),
        "follow": brand_social(),
    }


def legal_hub_manifest() -> dict[str, Any]:
    return {
        "title": "Legal",
        "lead": "Policies for Trust OS — research tool, not investment advice.",
        "pages": [
            {"id": "terms", "label": "Terms of Service", "href": "/terms"},
            {"id": "privacy", "label": "Privacy Policy", "href": "/privacy"},
            {"id": "cookies", "label": "Cookies", "href": "/cookies"},
            {"id": "disclaimer", "label": "Risk Disclaimer", "href": "/disclaimer"},
            {"id": "refund", "label": "Refund Policy", "href": "/refund"},
            {"id": "sla", "label": "Service Level Agreement", "href": "/sla"},
            {"id": "msa", "label": "Master Service Agreement", "href": "/msa"},
            {"id": "compliance", "label": "Anti-Hype Compliance", "href": "/compliance"},
            {"id": "complaints", "label": "Complaints", "href": "/complaints"},
        ],
    }


def submit_feedback(
    *,
    category: str,
    message: str,
    email: str = "",
    page: str = "",
) -> dict[str, Any]:
    """Persist feedback/suggestions; optionally enqueue email to support."""
    cat = (category or "suggestion").strip().lower()[:40] or "suggestion"
    msg = (message or "").strip()
    if len(msg) < 8:
        raise ValueError("Message must be at least 8 characters")
    if len(msg) > 4000:
        raise ValueError("Message too long (max 4000)")
    email_s = (email or "").strip()[:200]
    page_s = (page or "").strip()[:200]
    # Reject obvious card-number patterns in free text
    digits = "".join(ch for ch in msg if ch.isdigit())
    if len(digits) >= 13:
        raise ValueError("Do not include card numbers or secrets in feedback")

    row = {
        "id": f"fb_{uuid4().hex[:12]}",
        "category": cat,
        "message": msg,
        "email": email_s or None,
        "page": page_s or None,
        "created_at": _utcnow(),
        "status": "received",
    }
    with _FEEDBACK_LOCK:
        _FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _FEEDBACK_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")

    contact = contact_channels()
    try:
        from email_outbox import enqueue_email

        enqueue_email(
            contact["support_email"],
            f"[BLACKDARK feedback/{cat}] {row['id']}",
            f"From: {email_s or 'anonymous'}\nPage: {page_s or '—'}\n\n{msg}",
            payload={"feedback_id": row["id"], "category": cat},
        )
        row["emailed"] = True
    except Exception:
        row["emailed"] = False
    return {
        "ok": True,
        "id": row["id"],
        "status": "received",
        "message": "Thanks — we read every suggestion. Do not send card numbers here.",
    }


def _database_engine() -> str:
    try:
        from postgres_backend import use_postgres

        return "postgresql" if use_postgres() else "sqlite"
    except Exception:
        return "sqlite"


def _viral_status() -> dict[str, Any]:
    try:
        from viral_capacity import viral_readiness_report

        raw = viral_readiness_report()
        return {
            "status": raw.get("status") or raw.get("overall") or "reported",
            "summary": raw.get("summary") or raw.get("headline") or raw.get("message"),
            "ha_required": bool(raw.get("ha_required") or raw.get("ha_prerequisites")),
        }
    except Exception:
        return {"status": "unavailable"}


def _billing_status() -> dict[str, Any]:
    try:
        from payments_usd import payments_architecture

        arch = payments_architecture()
        ops = arch.get("ops_readiness") or {}
        sec = arch.get("security") or {}
        launch_ready = bool(ops.get("launch_ready"))
        return {
            "currency": arch.get("currency_code") or arch.get("currency") or "USD",
            "status": "operational" if launch_ready else "degraded",
            "active_provider": arch.get("active_provider"),
            "billing_configured": bool(arch.get("billing_configured")),
            "pci_posture": sec.get("pci_target") or sec.get("pci_saq") or "SAQ_A",
        }
    except Exception:
        return {
            "currency": "USD",
            "status": "reported",
            "pci_posture": "SAQ_A_hosted_checkout",
            "note": "Card data never stored on BLACKDARK servers",
        }


def _overall_status(components: list[dict[str, Any]]) -> str:
    bad = {"down", "fail", "failed", "error", "critical", "outage"}
    overall = "operational"
    for component in components:
        status = str(component.get("status") or "").lower()
        if status in bad:
            return "outage"
        if status in {"degraded", "warn", "warning", "partial", "unavailable"}:
            overall = "degraded"
    return overall


def public_status_report(*, fast: bool = False) -> dict[str, Any]:
    """Aggregate non-secret readiness for /status — never expose keys."""
    viral = (
        {"status": "reported", "summary": "See /health/viral for capacity detail."}
        if fast
        else _viral_status()
    )
    billing = _billing_status()
    db_engine = _database_engine()

    components = [
        {"id": "api", "label": "API process", "status": "operational"},
        {"id": "database", "label": f"Database ({db_engine})", "status": "operational"},
        {
            "id": "viral",
            "label": "Viral launch capacity",
            "status": viral.get("status") or "unknown",
        },
        {
            "id": "billing",
            "label": "USD billing posture",
            "status": billing.get("status") or "reported",
        },
    ]
    return {
        "product": "BLACKDARK Trust OS",
        "overall": _overall_status(components),
        "updated_at": _utcnow(),
        "components": components,
        "viral": viral,
        "billing": billing,
        "honesty": {
            "secrets_exposed": False,
            "guaranteed_uptime_sla": False,
            "note": "Public status is engineering posture, not a contractual SLA unless contracted.",
        },
        "links": {
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "health_viral": "/health/viral",
            "viral_api": "/api/viral/readiness",
            "faq": "/faq",
            "contact": "/contact",
        },
    }
