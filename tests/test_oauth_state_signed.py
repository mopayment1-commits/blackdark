"""Signed OAuth state must not require Postgres on callback validation."""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-oauth-signed")


@pytest.mark.asyncio
async def test_expired_signed_oauth_state_rejects_without_db(monkeypatch):
    import identity_service as ids

    async def _no_db(**_kwargs):
        raise OSError("[Errno -2] Name or service not known")

    import database

    monkeypatch.setattr(database, "consume_oauth_state", _no_db)

    state = ids.mint_signed_oauth_state("google")
    # Force expiry without touching DB.
    token = state[len(ids._OAUTH_STATE_PREFIX) :]
    import base64

    padded = token + "=" * (-len(token) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    parts = decoded.split("|")
    parts[1] = str(int((ids._utcnow() - timedelta(minutes=1)).timestamp()))
    body = "|".join(parts[:3])
    import hashlib
    import hmac

    sig = hmac.new(ids._oauth_state_pepper(), body.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    expired_raw = base64.urlsafe_b64encode(f"{body}|{sig}".encode("utf-8")).decode("ascii").rstrip("=")
    expired = f"{ids._OAUTH_STATE_PREFIX}{expired_raw}"

    with pytest.raises(ValueError, match="Invalid or expired"):
        await ids.validate_oauth_state_async("google", expired)


@pytest.mark.asyncio
async def test_valid_signed_oauth_state_skips_db(monkeypatch):
    import identity_service as ids

    async def _no_db(**_kwargs):
        raise OSError("[Errno -2] Name or service not known")

    import database

    monkeypatch.setattr(database, "consume_oauth_state", _no_db)
    state = ids.mint_signed_oauth_state("google")
    await ids.validate_oauth_state_async("google", state)
