"""Broadcast email to everyone on the join-waitlist table."""

from __future__ import annotations

import os
from typing import Any

from database import fetch_waitlist_emails


async def waitlist_newsletter_summary() -> dict[str, Any]:
    from database import db_count_waitlist

    count = await db_count_waitlist()
    preview = (await fetch_waitlist_emails())[:5]
    return {"count": count, "preview_emails": preview}


async def send_waitlist_newsletter(subject: str, message: str) -> dict[str, Any]:
    subject = (subject or "").strip()
    message = (message or "").strip()
    if not subject:
        raise ValueError("subject_required")
    if not message:
        raise ValueError("message_required")

    recipients = await fetch_waitlist_emails()
    total = len(recipients)
    if total == 0:
        return {
            "total": 0,
            "sent": 0,
            "failed": 0,
            "delivery": "none",
        }

    from alert_service import send_email_alert
    from email_outbox import enqueue_email

    smtp_configured = bool(os.getenv("SMTP_HOST", "").strip())
    sent = 0
    failed = 0
    delivery = "smtp" if smtp_configured else "outbox"

    for to_email in recipients:
        if smtp_configured:
            ok = send_email_alert(to_email, subject, message)
            if ok:
                sent += 1
            else:
                failed += 1
            continue
        row = enqueue_email(
            to_email,
            subject,
            message,
            payload={"kind": "waitlist_newsletter"},
        )
        if row.get("status") == "queue_failed":
            failed += 1
        else:
            sent += 1

    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "delivery": delivery,
    }
