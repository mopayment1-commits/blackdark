"""Support handoff and help/status linkage (ERR-048, ERR-049)."""

from __future__ import annotations

from typing import Any

from timezone.canonical import format_api_timestamp, utc_now


def support_handoff(
    *,
    correlation_id: str,
    component: str,
    action: str,
    summary_key: str,
    lang: str | None = None,
) -> dict[str, Any]:
    reference = correlation_id.replace("bd-", "SR-")[:12].upper()
    payload: dict[str, Any] = {
        "support_reference": reference,
        "timestamp": format_api_timestamp(utc_now()),
        "component": component,
        "action": action,
        "summary_key": summary_key,
        "links": {
            "status": "/status",
            "help": "/faq",
            "contact": "/contact",
        },
    }
    try:
        from i18n_service import t

        payload["summary"] = t(summary_key, lang)
    except Exception:
        payload["summary"] = summary_key
    return payload
