"""Secure Google account linking — ID-007, ID-008."""

from __future__ import annotations

from typing import Any


async def validate_google_id_token(id_token: str) -> dict[str, Any]:
    """Server-side Google OIDC validation when ID token is supplied."""
    import httpx

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
    if resp.status_code != 200:
        raise ValueError("Invalid Google ID token")
    data = resp.json()
    client_id = __import__("os").getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip()
    if client_id and data.get("aud") != client_id:
        raise ValueError("Google token audience mismatch")
    if data.get("email_verified") not in {True, "true", "True", "1"}:
        raise ValueError("Google email not verified")
    return {
        "provider": "google",
        "subject": str(data.get("sub") or ""),
        "email": str(data.get("email") or "").lower(),
        "name": str(data.get("name") or ""),
        "email_verified": True,
    }


async def secure_oauth_login(profile: dict[str, Any], *, linking_user_id: int | None = None) -> dict[str, Any]:
    """Link or create user by provider subject — never blind email merge."""
    from auth_service import create_session, resolve_user_tier
    from database import create_oauth_user, fetch_user_by_email, fetch_user_by_id, touch_user_login
    from identity.account_states import can_authenticate
    from identity.identity_audit import record_identity_event
    from identity.provider_registry import find_user_by_provider, link_provider

    provider = str(profile["provider"])
    subject = str(profile.get("subject") or "")
    email = str(profile.get("email") or "").lower()
    name = str(profile.get("name") or "")

    user = await find_user_by_provider(provider, subject)
    if user is None and linking_user_id:
        actor = await fetch_user_by_id(linking_user_id)
        if not actor:
            raise ValueError("Linking account not found")
        await link_provider(
            linking_user_id,
            provider=provider,
            provider_subject=subject,
            require_step_up=True,
            actor_user={**actor, "step_up_at": actor.get("step_up_at")},
        )
        user = await fetch_user_by_id(linking_user_id)
    elif user is None:
        by_email = await fetch_user_by_email(email)
        if by_email:
            raise ValueError(
                "An account with this email exists. Sign in and link Google from Profile → Security."
            )
        uid = await create_oauth_user(email, name, provider, subject)
        user = await fetch_user_by_id(uid)
        await link_provider(uid, provider=provider, provider_subject=subject, require_step_up=False)
    if not user or not can_authenticate(user.get("account_state")):
        raise ValueError("Account cannot authenticate")

    user_id = int(user["id"])
    await touch_user_login(user_id)
    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    await record_identity_event(event_type="login.success", user_id=user_id, detail={"method": f"oauth:{provider}"})
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {
            "id": user_id,
            "email": email,
            "name": user.get("name") or name,
            "tier": tier,
            "auth_method": f"oauth:{provider}",
        },
    }
