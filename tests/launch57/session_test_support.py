"""Helpers for Launch-57 tests requiring a validated server-side session."""

from __future__ import annotations

import uuid

from starlette.testclient import TestClient


def ensure_registered_session(client: TestClient, *, prefix: str = "launch57-test") -> TestClient:
    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePass1234!",
            "accepted_terms": True,
        },
        headers={"Origin": "https://testserver"},
    )
    return client
