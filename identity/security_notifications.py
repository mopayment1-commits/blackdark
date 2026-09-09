"""Localized security notifications — ID-044."""

from __future__ import annotations

from typing import Any

_EVENT_KEYS = {
    "security.new_device": ("notification.new_device.title", "notification.new_device.body"),
    "security.password_changed": ("notification.password_changed.title", "notification.password_changed.body"),
    "security.email_changed": ("notification.email_changed.title", "notification.email_changed.body"),
    "security.mfa_changed": ("notification.mfa_changed.title", "notification.mfa_changed.body"),
    "security.passkey_added": ("notification.passkey_added.title", "notification.passkey_added.body"),
    "security.passkey_removed": ("notification.passkey_removed.title", "notification.passkey_removed.body"),
    "security.provider_linked": ("notification.provider_linked.title", "notification.provider_linked.body"),
    "security.provider_unlinked": ("notification.provider_unlinked.title", "notification.provider_unlinked.body"),
    "security.deletion_requested": ("notification.deletion_requested.title", "notification.deletion_requested.body"),
    "security.compromise_response": ("notification.compromise_response.title", "notification.compromise_response.body"),
}


async def notify_security_event(user_id: int, event_key: str, *, actor: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    from database import fetch_user_by_id
    from i18n_enforcement import localize_email, localize_notification

    user = actor or await fetch_user_by_id(user_id)
    if not user:
        return {"sent": False}
    lang = user.get("ui_lang") or "en"
    tz_name = user.get("timezone") or "UTC"
    keys = _EVENT_KEYS.get(event_key)
    if not keys:
        return {"sent": False, "reason": "unknown_event"}
    title_key, body_key = keys
    fmt_kwargs = dict(kwargs)
    if fmt_kwargs.get("occurred_at"):
        from timezone.format import format_email_time

        fmt_kwargs["occurred_at_display"] = format_email_time(
            str(fmt_kwargs["occurred_at"]), lang=lang, tz_name=tz_name
        )
    note = localize_notification(lang, title_key, body_key, **fmt_kwargs)
    mail = localize_email(lang, title_key, body_key, **fmt_kwargs)
    try:
        from alert_service import dispatch_alert

        await dispatch_alert(
            "",
            "",
            lang=lang,
            title_key=title_key,
            body_key=body_key,
            channels=["in_app"],
            **kwargs,
        )
    except Exception:
        pass
    try:
        from email_outbox import enqueue_localized_email

        enqueue_localized_email(
            str(user.get("email") or ""),
            lang=lang,
            subject_key=title_key,
            body_key=body_key,
            payload={"kind": "security", "event": event_key, **kwargs},
        )
    except Exception:
        pass
    return {"sent": True, "locale": lang, "title": note["title"]}
