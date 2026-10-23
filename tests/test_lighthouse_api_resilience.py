"""Landing Lighthouse — APIs must not 500 for anonymous homepage clients."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_entitlements_and_pulse_never_500_for_anonymous():
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    for path in (
        "/api/entitlements/me",
        "/api/entitlements/refresh-policy",
        "/api/trust-pulse?symbol=BTC&lang=en&ux_mode=beginner",
    ):
        res = client.get(path)
        assert res.status_code == 200, (path, res.status_code, res.text[:200])
