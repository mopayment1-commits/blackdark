"""Shared FastAPI dependencies for API routers."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException


async def optional_user(authorization: str | None = Header(None, alias="Authorization")) -> dict | None:
    from auth_service import get_user_from_token

    if not authorization:
        return None
    token = authorization.removeprefix("Bearer ")
    return await get_user_from_token(token.strip())


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
    session_id = (user or {}).get("token") if not email else None
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
