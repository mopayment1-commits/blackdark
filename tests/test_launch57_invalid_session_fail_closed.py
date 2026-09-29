"""Launch-57 — invalid session must not access protected command-home (AV-06)."""

from __future__ import annotations

import uuid

from starlette.testclient import TestClient


def test_invalid_bd_token_denied_on_command_home():
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.clear()
    client.cookies.set("bd_token", f"invalid-{uuid.uuid4().hex}")
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 401


def test_no_token_denied_on_command_home():
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 401
