"""Commercial support operational configuration — COM-SUPPORT RVM gate."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

DEFAULT_SUPPORT_EMAIL = "mopayment1@gmail.com"
DEFAULT_SUPPORT_OWNER = "Project owner/operator"
DEFAULT_SUPPORT_HOURS = "10:00 AM – 10:00 PM Cairo Time, daily"
DEFAULT_URGENT_SUBJECT_PREFIX = "URGENT"
SUPPORT_TIERS_DOC = "docs/support/SUPPORT_TIERS.md"


def _env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def commercial_support_config() -> dict[str, Any]:
    email = _env("SUPPORT_EMAIL", DEFAULT_SUPPORT_EMAIL).lower()
    return {
        "support_email": email,
        "support_owner": _env("SUPPORT_OWNER", DEFAULT_SUPPORT_OWNER),
        "support_hours": _env("SUPPORT_HOURS", DEFAULT_SUPPORT_HOURS),
        "urgent_escalation": {
            "channel": "email",
            "address": email,
            "subject_prefix": _env("SUPPORT_URGENT_SUBJECT_PREFIX", DEFAULT_URGENT_SUBJECT_PREFIX),
            "instructions": (
                f"Email {email} with subject line starting with "
                f"{_env('SUPPORT_URGENT_SUBJECT_PREFIX', DEFAULT_URGENT_SUBJECT_PREFIX)}"
            ),
        },
    }


def _doc_operational_published(cfg: dict[str, Any]) -> bool:
    path = Path(__file__).resolve().parent / SUPPORT_TIERS_DOC
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    email = cfg["support_email"]
    prefix = cfg["urgent_escalation"]["subject_prefix"]
    return (
        email.lower() in text.lower()
        and cfg["support_owner"].lower() in text.lower()
        and "cairo" in text.lower()
        and prefix.upper() in text.upper()
    )


def commercial_support_status() -> dict[str, Any]:
    cfg = commercial_support_config()
    from site_services import contact_channels

    contact = contact_channels()
    contact_published = contact.get("support_email", "").lower() == cfg["support_email"]
    doc_published = _doc_operational_published(cfg)
    operational_ready = (
        bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cfg["support_email"]))
        and bool(cfg["support_owner"])
        and bool(cfg["support_hours"])
        and bool(cfg["urgent_escalation"]["subject_prefix"])
        and doc_published
        and contact_published
        and bool(contact.get("support_hours"))
        and bool(contact.get("urgent_escalation"))
    )
    return {
        "surface": "commercial_support",
        "product_complete": True,
        "operational_ready": operational_ready,
        "config": cfg,
        "published": {
            "support_tiers_doc": doc_published,
            "contact_page": contact_published,
        },
        "doc_path": str(Path(__file__).resolve().parent / SUPPORT_TIERS_DOC),
    }
