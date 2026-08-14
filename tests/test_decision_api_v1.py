"""Decision API v1 — commercial Financial Intelligence contract."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from public_api_docs import path_is_public


@pytest.fixture
def admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    monkeypatch.setenv("DECISION_API_KEY_PEPPER", "unit-test-decision-api-pepper")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "unit-test-session-pepper")
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)


@pytest.fixture
def client(admin_env):
    asyncio.run(_init_db())
    from dashboard import app

    return TestClient(app)


async def _init_db() -> None:
    from database import init_db

    await init_db()


def test_public_openapi_omits_key_issuance():
    assert path_is_public("/api/v1/oracle/BTC")
    assert path_is_public("/api/v1/openapi.json")
    assert path_is_public("/api/v1/audit")
    assert path_is_public("/api/v1/usage")
    assert path_is_public("/api/v1/webhooks")
    assert not path_is_public("/api/v1/keys")
    assert not path_is_public("/api/v1/keys/dak_x/revoke")


def test_discovery_is_public(client):
    r = client.get("/api/v1")
    assert r.status_code == 200
    body = r.json()
    assert body["api_version"] == "v1"
    assert body["contract"] == "decision-api-v1"
    assert "/api/v1/feed" in body["endpoints"]["feed"]


def test_accuracy_requires_api_key(client):
    r = client.get("/api/v1/accuracy")
    assert r.status_code == 401
    body = r.json()
    assert body["code"] == "unauthorized"
    assert body["request_id"]
    assert r.headers.get("X-API-Version") == "v1"
    assert r.headers.get("X-Request-Id")


def test_invalid_key_rejected(client):
    r = client.get("/api/v1/accuracy", headers={"X-API-Key": "bd_live_this_is_not_a_real_key_value"})
    assert r.status_code == 401
    assert r.json()["code"] == "unauthorized"


def test_issue_authenticate_revoke_and_feed(client):
    issued = client.post(
        "/api/v1/keys",
        headers={"X-Admin-Key": "z" * 24},
        json={"org_id": "org_desk_alpha", "name": "desk-prod", "environment": "live"},
    )
    assert issued.status_code == 200, issued.text
    payload = issued.json()
    assert payload["api_key"].startswith("bd_live_")
    assert payload["signing_secret"]
    assert payload["shown_once"] is True
    assert "oracle:read" in payload["scopes"]
    key = payload["api_key"]
    public_id = payload["id"]

    me = client.get("/api/v1/me", headers={"X-API-Key": key})
    assert me.status_code == 200, me.text
    assert me.json()["key"]["org_id"] == "org_desk_alpha"
    assert me.headers.get("X-RateLimit-Limit")

    listed = client.get("/api/v1/keys", headers={"X-Admin-Key": "z" * 24})
    assert listed.status_code == 200
    assert all("api_key" not in row and "key_hash" not in row for row in listed.json()["keys"])

    with patch(
        "database.fetch_institutional_feed_rows",
        new_callable=AsyncMock,
        return_value=[{"flow_type": "whale_alert"}],
    ):
        feed = client.get("/api/v1/feed", headers={"X-API-Key": key})
    assert feed.status_code == 200, feed.text
    body = feed.json()
    assert body["api_version"] == "v1"
    assert body["org_id"] == "org_desk_alpha"
    assert body["signature"]
    assert body["licensed_use"] == "internal_decision_support"
    assert body["data_license"]["class"] == "internal_decision_support"
    assert body["data_license"]["redistribution_allowed"] is False

    revoked = client.post(
        f"/api/v1/keys/{public_id}/revoke",
        headers={"X-Admin-Key": "z" * 24},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    denied = client.get("/api/v1/me", headers={"X-API-Key": key})
    assert denied.status_code == 401


def test_issuance_is_admin_only(client):
    r = client.post("/api/v1/keys", json={"org_id": "org_x", "name": "nope"})
    assert r.status_code == 403


def test_scope_enforced(client):
    issued = client.post(
        "/api/v1/keys",
        headers={"X-Admin-Key": "z" * 24},
        json={
            "org_id": "org_scoped",
            "name": "accuracy-only",
            "environment": "test",
            "scopes": ["accuracy:read"],
        },
    )
    assert issued.status_code == 200, issued.text
    key = issued.json()["api_key"]
    assert key.startswith("bd_test_")
    denied = client.get("/api/v1/feed", headers={"X-API-Key": key})
    assert denied.status_code == 403
    assert denied.json()["code"] == "insufficient_scope"


def test_universe_not_licensed(client, monkeypatch):
    monkeypatch.setenv("DECISION_API_UNIVERSE", "BTC,ETH")
    issued = client.post(
        "/api/v1/keys",
        headers={"X-Admin-Key": "z" * 24},
        json={"org_id": "org_uni", "name": "uni", "environment": "test"},
    )
    key = issued.json()["api_key"]
    r = client.get("/api/v1/oracle/DOGE", headers={"X-API-Key": key})
    assert r.status_code == 403
    assert r.json()["code"] == "universe_not_licensed"


def test_oracle_happy_path_mocked(client):
    issued = client.post(
        "/api/v1/keys",
        headers={"X-Admin-Key": "z" * 24},
        json={"org_id": "org_or", "name": "oracle", "environment": "test"},
    )
    key = issued.json()["api_key"]
    ticker = {"price": 100.0, "volume": 10.0, "quote_volume": 1000.0, "change_24h": 1.2}
    unified = {
        "opportunity_score": 61,
        "verdict": "BUY",
        "confidence": 0.4,
        "engine": "unified_multimodal_v1",
        "market_regime": "risk_on",
    }
    with (
        patch("market_context.fetch_binance_ticker", new_callable=AsyncMock, return_value=ticker),
        patch("oracle_unified.compute_unified_oracle", new_callable=AsyncMock, return_value=unified),
    ):
        r = client.get("/api/v1/oracle/BTC", headers={"X-API-Key": key})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["asset"] == "BTC"
    assert body["opportunity_score"] == 61
    assert body["verdict"]
    assert body["decision_certificate"]
    assert body["canonical_market_state"]
    assert body["data_license"]["redistribution_allowed"] is False
    assert body["decision_certificate"].get("data_license") == "internal_decision_support"
    assert "Not financial advice" in body["disclaimer"]


def test_ws_rejects_query_api_key(client):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/feed/ws?api_key=bd_live_should_not_work"):
            pass


def test_legacy_b2b_deprecation_headers(client):
    r = client.get("/api/b2b/info")
    assert r.status_code == 200
    assert r.headers.get("Deprecation") == "true"
    assert "/api/v1/feed" in (r.headers.get("Link") or "")
    assert r.json()["successor"] == "/api/v1/feed"


def test_track_record_backfill_requires_admin(client):
    r = client.post("/api/oracle/track-record/backfill")
    assert r.status_code == 403


def test_v1_openapi_omits_issuance_and_deny_paths(client):
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert any(p.startswith("/api/v1/oracle") for p in paths)
    assert any(p.startswith("/api/v1/audit") for p in paths)
    assert any(p.startswith("/api/v1/webhooks") for p in paths)
    assert not any(p.startswith("/api/v1/keys") for p in paths)
    joined = " ".join(paths)
    assert "/execution" not in joined
    assert "/vault" not in joined


def test_sdk_sends_api_key_header():
    from sdk.blackdark.client import BlackdarkClient

    c = BlackdarkClient("http://example.invalid", api_key="bd_live_abc")
    headers = c._headers()
    assert headers["X-API-Key"] == "bd_live_abc"
    assert headers["Authorization"] == "Bearer bd_live_abc"
    assert callable(c.audit)
    assert callable(c.usage)
    assert callable(c.register_webhook)


def test_key_hash_is_not_plaintext():
    from api.v1.keys import generate_api_key, hash_api_key

    plaintext, prefix = generate_api_key(environment="live")
    digest = hash_api_key(plaintext)
    assert plaintext not in digest
    assert digest != plaintext
    assert prefix.startswith("bd_live_")
    assert hash_api_key(plaintext) == digest
    assert len(digest) == 64


def _issue(client: TestClient, org_id: str, name: str = "desk") -> dict:
    issued = client.post(
        "/api/v1/keys",
        headers={"X-Admin-Key": "z" * 24},
        json={"org_id": org_id, "name": name, "environment": "test"},
    )
    assert issued.status_code == 200, issued.text
    return issued.json()


async def _audit_row_count() -> int:
    from database import get_connection

    async with get_connection() as db:
        row = await (await db.execute("SELECT COUNT(*) FROM decision_api_audit")).fetchone()
    return int(next(iter(dict(row).values())))


def test_audit_persists_401_and_200(client):
    before = asyncio.run(_audit_row_count())
    denied = client.get("/api/v1/me")
    assert denied.status_code == 401
    after_401 = asyncio.run(_audit_row_count())
    assert after_401 == before + 1

    key = _issue(client, "org_audit_persist")["api_key"]
    after_issue = asyncio.run(_audit_row_count())
    me = client.get("/api/v1/me", headers={"X-API-Key": key})
    assert me.status_code == 200
    after_200 = asyncio.run(_audit_row_count())
    assert after_200 == after_issue + 1

    audit = client.get("/api/v1/audit", headers={"X-API-Key": key})
    assert audit.status_code == 200, audit.text
    events = audit.json()["events"]
    paths = {row["path"] for row in events}
    assert "/api/v1/me" in paths
    assert all(row["org_id"] == "org_audit_persist" for row in events)
    assert all("?" not in (row["path"] or "") for row in events)


def test_audit_is_org_scoped(client):
    key_a = _issue(client, "org_alpha_audit")["api_key"]
    key_b = _issue(client, "org_bravo_audit")["api_key"]
    client.get("/api/v1/me", headers={"X-API-Key": key_a})
    client.get("/api/v1/me", headers={"X-API-Key": key_b})
    audit_a = client.get("/api/v1/audit", headers={"X-API-Key": key_a}).json()["events"]
    assert all(row["org_id"] == "org_alpha_audit" for row in audit_a)
    assert all(row["org_id"] != "org_bravo_audit" for row in audit_a)


def test_usage_history_after_calls(client):
    key = _issue(client, "org_usage_desk")["api_key"]
    client.get("/api/v1/me", headers={"X-API-Key": key})
    usage = client.get("/api/v1/usage", headers={"X-API-Key": key})
    assert usage.status_code == 200, usage.text
    body = usage.json()
    assert body["org_id"] == "org_usage_desk"
    assert body["history"]
    assert int(body["history"][0]["count"]) >= 1


def test_webhook_register_signed_delivery_and_ssrf(client):
    from api.v1.webhooks import sign_webhook_body, validate_webhook_url, verify_webhook_signature

    with pytest.raises(ValueError):
        validate_webhook_url("http://169.254.169.254/")
    with pytest.raises(ValueError):
        validate_webhook_url("https://169.254.169.254/latest/meta-data/")

    ts = "1700000000"
    body = '{"ok":true}'
    sig = sign_webhook_body("unit-secret", ts, body)
    assert sig.startswith("sha256=")
    with patch("api.v1.webhooks.time.time", return_value=1_700_000_000):
        assert verify_webhook_signature(
            signing_secret="unit-secret",
            timestamp=ts,
            body=body,
            signature=sig,
        )
        assert not verify_webhook_signature(
            signing_secret="unit-secret",
            timestamp=ts,
            body=body,
            signature="sha256=deadbeef",
        )

    issued = _issue(client, "org_hooks")
    key = issued["api_key"]
    with patch("api.v1.webhooks._post_webhook", new_callable=AsyncMock, return_value=204) as posted:
        created = client.post(
            "/api/v1/webhooks",
            headers={"X-API-Key": key},
            json={"url": "http://127.0.0.1:9/hook", "events": ["ping", "oracle.decision"]},
        )
        assert created.status_code == 200, created.text
        hook_id = created.json()["webhook"]["id"]
        ping = client.post(
            "/api/v1/webhooks/test",
            headers={"X-API-Key": key},
            json={"webhook_id": hook_id},
        )
        assert ping.status_code == 200, ping.text
        deliveries = ping.json()["deliveries"]
        assert deliveries and deliveries[0]["ok"] is True
        assert posted.await_count == 1
        _url, raw_body, headers = posted.await_args.args
        assert _url == "http://127.0.0.1:9/hook"
        assert headers["X-Blackdark-Event"] == "ping"
        assert verify_webhook_signature(
            signing_secret=issued["signing_secret"],
            timestamp=headers["X-Blackdark-Timestamp"],
            body=raw_body.decode("utf-8"),
            signature=headers["X-Blackdark-Signature"],
        )
        listed = client.get("/api/v1/webhooks", headers={"X-API-Key": key})
        assert listed.status_code == 200
        disabled = client.delete(f"/api/v1/webhooks/{hook_id}", headers={"X-API-Key": key})
        assert disabled.status_code == 200
        assert disabled.json()["status"] == "disabled"


def test_webhook_rejects_metadata_url_on_register(client):
    key = _issue(client, "org_ssrf")["api_key"]
    r = client.post(
        "/api/v1/webhooks",
        headers={"X-API-Key": key},
        json={"url": "http://169.254.169.254/latest/meta-data/"},
    )
    assert r.status_code == 400
    assert r.json()["code"] in {"https_required", "webhook_host_forbidden", "webhook_url_invalid"}
