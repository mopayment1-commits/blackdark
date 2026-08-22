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


def brand_social() -> list[dict[str, str]]:
    """Official brand profiles (Follow us) — configure via env."""
    items = [
        {
            "id": "x",
            "label": "X",
            "href": _env("BRAND_SOCIAL_X", "https://x.com/blackdark"),
        },
        {
            "id": "telegram",
            "label": "Telegram",
            "href": _env("BRAND_SOCIAL_TELEGRAM", "https://t.me/blackdark"),
        },
        {
            "id": "linkedin",
            "label": "LinkedIn",
            "href": _env(
                "BRAND_SOCIAL_LINKEDIN",
                "https://www.linkedin.com/company/blackdark",
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
    sales = _env("SALES_EMAIL", "sales@blackdark.io")
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
        "q": "What is Proof Pass (Free)?",
        "a": "Prove lens: understandable Why + shareable Decision Certificate, limited certified decisions per day, with a Free Proof watermark.",
    },
    {
        "q": "What do I get with Decision Pro ($29 USD)?",
        "a": "Operate lens: daily habit depth — unlimited Oracle (no tight Free ceiling), Portfolio AI, alerts, no Free watermark, plus AI Chat. 7-day trial available.",
    },
    {
        "q": "What is Decision Desk?",
        "a": "Desk lens ($49 USD): packaging to convince someone else — Signal-to-Noise, Stealth views, Evidence pack, API priority.",
    },
    {
        "q": "How do funds engage?",
        "a": "Room lens — Data Room and Integration Addendum. Talk to us; not self-serve Checkout.",
    },
    {
        "q": "What can I share on social / WhatsApp?",
        "a": "Share Proof Cards and Ledger snapshots (decision + short why + verify link). Do not share API keys or private holdings.",
    },
    {
        "q": "Where is AI Chat and who can use it?",
        "a": "Inside the dashboard Operate/Desk experience. Available on Decision Pro and Decision Desk. It explains the current decision context — it does not replace the Oracle or guarantee outcomes.",
    },
    {
        "q": "How do I reset my password?",
        "a": "Use Forgot password on the Login page. We email a one-time link (SMTP or queued outbox).",
    },
    {
        "q": "How do refunds work?",
        "a": "See /refund. Self-serve plans are USD monthly; trials convert unless cancelled. Refunds via Lemon/Stripe for clear billing errors or as required by law.",
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
            {"label": "Trust Pulse", "href": "/dashboard?lens=prove#trust-pulse"},
            {"label": "Decide", "href": "/dashboard?lens=prove#decide"},
            {"label": "Verify", "href": "/oracle-accuracy"},
            {"label": "Dashboard", "href": "/dashboard"},
            {"label": "Pricing", "href": "/#pricing"},
            {"label": "AI Chat", "href": "/dashboard?lens=operate#ai-chat"},
        ],
        "trust": [
            {"label": "How it works", "href": "/how-it-works"},
            {"label": "Capabilities", "href": "/capabilities"},
            {"label": "FAQ", "href": "/faq"},
            {"label": "Status", "href": "/status"},
            {"label": "Changelog", "href": "/changelog"},
            {"label": "Compliance", "href": "/compliance"},
        ],
        "company": [
            {"label": "About", "href": "/about"},
            {"label": "Contact", "href": "/contact"},
            {"label": "Feedback", "href": "/feedback"},
            {"label": "Complaints", "href": "/complaints"},
            {"label": "Data Room", "href": "/data-room"},
        ],
        "legal": [
            {"label": "Legal hub", "href": "/legal"},
            {"label": "Terms", "href": "/terms"},
            {"label": "Privacy", "href": "/privacy"},
            {"label": "Cookies", "href": "/cookies"},
            {"label": "Refund", "href": "/refund"},
            {"label": "Disclaimer", "href": "/disclaimer"},
        ],
        "follow": brand_social(),
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
    return {
        "title": "About BLACKDARK",
        "lead": (
            "BLACKDARK is a Trust OS for crypto decision intelligence: "
            "one clear decision, a reviewable why, and a shareable proof — "
            "verified on a public accuracy ledger."
        ),
        "difference": (
            "Competitors sell charts, data feeds, or opaque scores. "
            "We sell a reviewable decision + Proof Card as the free viral wedge, "
            "and depth of trust as the paid product."
        ),
        "lenses": "Prove → Operate → Desk → Room",
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


def public_status_report() -> dict[str, Any]:
    """Aggregate non-secret readiness for /status — never expose keys."""
    viral = _viral_status()
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
