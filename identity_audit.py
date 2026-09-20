"""Identity auth audit trail — registration, login, recovery, password change."""

from __future__ import annotations

from typing import Any


def _client_ip(request: Any | None) -> str | None:
    if request is None:
        return None
    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip and getattr(request, "client", None):
        ip = request.client.host or ""
    return ip or None


def log_identity_auth_event(
    kind: str,
    *,
    actor: str | None = None,
    user_id: int | None = None,
    ip: str | None = None,
    request: Any | None = None,
    detail: dict[str, Any] | None = None,
    severity: str = "info",
) -> dict[str, Any]:
    from security_events import record_security_event

    payload = dict(detail or {})
    if user_id is not None:
        payload["user_id"] = user_id
    return record_security_event(
        kind,
        severity=severity,
        actor=actor,
        ip=ip or _client_ip(request),
        detail=payload,
    )
