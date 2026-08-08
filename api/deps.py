"""Shared FastAPI dependencies for API routers."""

from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException


async def optional_user(
    authorization: str | None = Header(None, alias="Authorization"),
    bd_token: str | None = Cookie(None, alias="bd_token"),
) -> dict | None:
    """Resolve user from Bearer token or HttpOnly bd_token cookie."""
    from auth_service import get_user_from_token

    token: str | None = None
    if authorization:
        token = authorization.removeprefix("Bearer ")
    elif bd_token:
        from security_middleware import cookie_to_session_bearer

        token = cookie_to_session_bearer(bd_token)
    if not token:
        return None
    return await get_user_from_token(token.strip())


def raw_bearer_or_cookie(
    authorization: str | None = Header(None, alias="Authorization"),
    bd_token: str | None = Cookie(None, alias="bd_token"),
) -> str | None:
    """Return the raw session token (for logout / revoke)."""
    if authorization:
        return (authorization.removeprefix("Bearer ")).strip()
    if bd_token:
        from security_middleware import cookie_to_session_bearer

        return cookie_to_session_bearer(bd_token) or None
    return None


def require_feature(feature: str):
    async def _dependency(user: dict | None = Depends(optional_user)) -> dict | None:
        from auth_service import feature_allowed

        if not feature_allowed(user, feature):
            tier = (user or {}).get("tier") or "free"
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "upgrade_required",
                    "feature": feature,
                    "current_tier": tier,
                    "message": f"This feature requires an upgrade. Current plan: {tier}.",
                    "upgrade_url": "/create-checkout-session?tier=pro",
                },
            )
        return user

    return _dependency


async def record_behavior(
    event_type: str,
    *,
    user: dict | None = None,
    asset: str | None = None,
    payload: dict | None = None,
) -> None:
    from behavior_data_service import record_behavior_event

    email = (user or {}).get("email")
    tier = (user or {}).get("tier")
    session_id = None
    await record_behavior_event(
        event_type,
        user_email=email,
        tier=tier,
        asset=asset,
        session_id=session_id,
        payload=payload,
    )
    try:
        from observability import increment_metric

        increment_metric("behavior_events_total")
    except Exception:
        pass
