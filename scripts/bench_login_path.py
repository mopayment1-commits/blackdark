#!/usr/bin/env python3
"""Measure login → dashboard path segment latencies (diagnostic only)."""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def main() -> None:
    from dashboard import app

    client = TestClient(app)
    email = f"bench-{uuid.uuid4().hex[:10]}@example.com"
    password = "SecurePass1234!"

    rows: list[tuple[str, float, str]] = []

    t0 = time.perf_counter()
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "accepted_terms": True,
            "accepted_privacy": True},
        headers={"Origin": "https://testserver"},
    )
    rows.append(("POST /api/auth/register (setup)", _ms(t0), str(reg.status_code)))

    t0 = time.perf_counter()
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers={"Origin": "https://testserver"},
    )
    rows.append(("POST /api/auth/login", _ms(t0), str(login.status_code)))

    t0 = time.perf_counter()
    dash = client.get("/dashboard", headers={"Accept": "text/html"})
    rows.append(("GET /dashboard (first HTML)", _ms(t0), str(dash.status_code)))

    t0 = time.perf_counter()
    home = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    rows.append(("GET /api/launch57/command-home", _ms(t0), str(home.status_code)))

    async def _google_callback_ms() -> float:
        import oauth_service

        async def fake_verify(_credential: str):
            return {
                "provider": "google",
                "subject": "bench-google",
                "email": f"g-{uuid.uuid4().hex[:8]}@example.com",
                "name": "Bench Google",
            }

        oauth_service.verify_google_credential = fake_verify
        t0 = time.perf_counter()
        client.post(
            "/login?plan=free",
            data={"credential": "x" * 40},
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "testserver"},
            follow_redirects=False,
        )
        return _ms(t0)

    rows.append(("POST /login Google callback", asyncio.run(_google_callback_ms()), "see status"))

    async def _spine_ms() -> float:
        from launch57.decision_common import load_decision_spine

        t0 = time.perf_counter()
        await load_decision_spine("BTC", {})
        return _ms(t0)

    rows.append(("load_decision_spine (server, command-home core)", asyncio.run(_spine_ms()), "internal"))

    print("| Step | ms | note |")
    print("|------|-----|------|")
    for step, ms, note in rows:
        print(f"| {step} | {ms} | {note} |")


if __name__ == "__main__":
    main()
