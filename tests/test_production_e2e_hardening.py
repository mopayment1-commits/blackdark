"""Production E2E hardening: market failover, Postgres health, register alias, dup signup."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


def _isolated_sqlite(tmp_path, monkeypatch, name: str) -> None:
    import config
    import database

    db_path = tmp_path / name
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("AUTH_TOKEN_IN_BODY", "true")
    asyncio.run(database.init_db())


def test_first_cell_reads_postgres_dict_and_sqlite_tuple():
    from database import _first_cell

    assert _first_cell((7,)) == 7
    assert _first_cell({"count": 4}) == 4
    assert _first_cell(None) is None


def test_increment_oracle_usage_survives_isolated_sqlite(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "oracle-usage.db")
    import asyncio
    import database

    n = asyncio.run(database.increment_oracle_usage("quota.e2e@example.com"))
    assert n >= 1
    used = asyncio.run(database.fetch_oracle_usage_today("quota.e2e@example.com"))
    assert used >= 1


def test_register_alias_is_not_404():
    from dashboard import app

    client = TestClient(app)
    resp = client.get("/register", follow_redirects=False)
    assert resp.status_code == 307
    assert "/login" in (resp.headers.get("location") or "")


def test_duplicate_register_is_400_not_500(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "e2e.db")
    from dashboard import app

    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    body = {
        "email": "dup.e2e@example.com",
        "password": "E2eHarden!Aa123456",
        "name": "Dup",
        "accepted_terms": True,
    }
    first = client.post("/api/auth/register", json=body, headers=origin)
    assert first.status_code == 200, first.text
    second = client.post("/api/auth/register", json=body, headers=origin)
    assert second.status_code == 400, second.text
    assert "already" in (second.json().get("detail") or "").lower()


def test_register_login_me_logout_cookie_journey(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "e2e-session.db")
    from dashboard import app

    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    email = "session.e2e@example.com"
    password = "E2eHarden!Aa123456"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "Sess", "accepted_terms": True},
        headers=origin,
    )
    assert reg.status_code == 200, reg.text
    assert client.cookies.get("bd_token")
    me_after_register = client.get("/api/auth/me")
    assert me_after_register.json().get("authenticated") is True
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers=origin,
    )
    assert login.status_code == 200, login.text
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json().get("authenticated") is True
    out = client.post("/api/auth/logout", headers=origin)
    assert out.status_code == 200
    me2 = client.get("/api/auth/me")
    assert me2.json().get("authenticated") is False


def test_production_http_cookie_when_secure_explicitly_disabled(tmp_path, monkeypatch):
    """ENV=production + COOKIE_SECURE=false must still persist HttpOnly session on HTTP."""
    _isolated_sqlite(tmp_path, monkeypatch, "e2e-http-prod.db")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_TOKEN_IN_BODY", "false")
    from dashboard import app

    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "http.prod.e2e@example.com",
            "password": "E2eHarden!Aa123456",
            "name": "HttpProd",
            "accepted_terms": True,
        },
        headers=origin,
    )
    assert reg.status_code == 200, reg.text
    assert "token" not in (reg.json() or {})
    set_cookie = (reg.headers.get("set-cookie") or "").lower()
    assert "bd_token=" in set_cookie
    assert "secure" not in set_cookie
    assert client.cookies.get("bd_token")
    me = client.get("/api/auth/me")
    assert me.json().get("authenticated") is True


@pytest.mark.asyncio
async def test_market_overview_failsover_when_primary_binance_empty(monkeypatch):
    import market_context as mc

    async def _empty(_session, host):
        if host == "api.binance.com":
            return None
        return [
            {
                "symbol": "BTCUSDT",
                "lastPrice": "63015.28",
                "priceChangePercent": "1.2",
                "quoteVolume": "25000000",
            }
        ]

    monkeypatch.setattr(mc, "_fetch_binance_24hr_rows", _empty)
    pack = await mc.fetch_binance_market_overview_pack(limit=5)
    assert pack["assets"]
    assert pack["assets"][0]["symbol"] == "BTC"
    assert pack["assets"][0]["price"] == 63015.28
    assert "binance.vision" in pack["data_source"] or pack["source_host"] == "data-api.binance.vision"


@pytest.mark.asyncio
async def test_database_health_postgres_url_does_not_raise(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/blackdark")
    from db_upgrade import database_health_report

    report = await database_health_report()
    assert report["engine"] == "postgresql"
    assert "postgres_pool" in report


def test_telegram_test_unauth_is_401():
    from dashboard import app

    client = TestClient(app)
    resp = client.post("/api/alerts/telegram/test", json={})
    assert resp.status_code == 401


def test_gtm_and_launch_do_not_500():
    from dashboard import app

    client = TestClient(app)
    gtm = client.get("/api/gtm/status")
    launch = client.get("/api/launch/readiness")
    assert gtm.status_code == 200
    assert launch.status_code == 200


def test_billing_status_does_not_500():
    from dashboard import app

    client = TestClient(app)
    resp = client.get("/api/billing/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "billing_configured" in body


def test_mfa_enroll_without_master_key_is_503_not_500(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "e2e-mfa.db")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    monkeypatch.delenv("SECRETS_VAULT_KEY", raising=False)
    monkeypatch.delenv("MFA_ENCRYPTION_KEY", raising=False)
    from dashboard import app

    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "mfa.e2e@example.com",
            "password": "E2eHarden!Aa123456",
            "name": "Mfa",
            "accepted_terms": True,
        },
        headers=origin,
    )
    assert reg.status_code == 200, reg.text
    enroll = client.post("/api/auth/mfa/enroll", headers=origin)
    assert enroll.status_code == 503
    assert "MFA" in (enroll.json().get("detail") or "")


def test_graphql_http_health_does_not_422_for_missing_request_query():
    from dashboard import app

    client = TestClient(app)
    resp = client.post("/graphql", json={"query": "{ health { status probe } }"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body.get("data") or {}).get("health", {}).get("status") == "ok"


def test_portfolio_analyze_accepts_holdings_object(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "e2e-port.db")
    from dashboard import app

    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "port.e2e@example.com",
            "password": "E2eHarden!Aa123456",
            "name": "Port",
            "accepted_terms": True,
            "plan": "pro",
        },
        headers=origin,
    )
    assert reg.status_code == 200, reg.text
    resp = client.post(
        "/portfolio/analyze",
        json={"holdings": [{"symbol": "BTC", "amount": 1}]},
        headers=origin,
    )
    assert resp.status_code == 200, resp.text
    assert "holdings" in resp.json() or "risk_score" in resp.json() or "plain" in resp.json()


def test_portfolio_analyze_accepts_asset_quantity_aliases(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "e2e-port-alias.db")
    from dashboard import app

    async def _fake_ticker(_pair):
        return {"price": 63000.0, "change_24h": 0.1, "source": "test"}

    monkeypatch.setattr("dashboard._fetch_binance_ticker", _fake_ticker)
    client = TestClient(app)
    origin = {"Origin": "https://testserver"}
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "port.alias@example.com",
            "password": "E2eHarden!Aa123456",
            "name": "Port",
            "accepted_terms": True,
            "plan": "pro",
        },
        headers=origin,
    )
    assert reg.status_code == 200, reg.text
    resp = client.post(
        "/portfolio/analyze",
        json={"holdings": [{"asset": "BTC", "quantity": 0.1}]},
        headers=origin,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("total_value", 0) > 0
    assert body.get("holdings")
    assert body["holdings"][0]["symbol"] == "BTC"


def test_product_honesty_surfaces_are_not_404():
    from dashboard import app

    client = TestClient(app)
    for path in (
        "/api/public/changed-mind",
        "/api/public/decision-graph",
        "/api/product/l2-remainder",
        "/api/product/capability-inventory",
        "/api/product/public-readiness",
    ):
        resp = client.get(path)
        assert resp.status_code == 200, (path, resp.status_code, resp.text[:200])
        body = resp.json()
        assert isinstance(body, dict)
        assert body.get("surface") or body.get("tracks") or body.get("items") is not None


@pytest.mark.asyncio
async def test_simulate_ticker_uses_market_context_failover(monkeypatch):
    from trade_simulator import _fetch_ticker

    async def _vision(_pair):
        return {"price": 63023.65, "change_24h": -0.8, "source": "binance:data-api.binance.vision"}

    import market_context as mc

    monkeypatch.setattr(mc, "fetch_binance_ticker", _vision)
    row = await _fetch_ticker("BTCUSDT")
    assert row is not None
    assert row["price"] == 63023.65


@pytest.mark.asyncio
async def test_binance_closes_failover_hosts(monkeypatch):
    from forecast_engine import _fetch_binance_closes

    calls: list[str] = []

    class _Resp:
        def __init__(self, status, payload):
            self.status = status
            self._payload = payload

        async def json(self):
            return self._payload

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class _Session:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def get(self, url):
            calls.append(url)
            if "api.binance.com" in url:
                return _Resp(451, [])
            rows = [[0, "1", "1", "1", str(100 + i), "1"] for i in range(30)]
            return _Resp(200, rows)

    import aiohttp

    monkeypatch.setattr(aiohttp, "ClientSession", _Session)
    closes = await _fetch_binance_closes("BTCUSDT", interval="1h", limit=30)
    assert len(closes) == 30
    assert any("data-api.binance.vision" in u for u in calls)


def test_public_accuracy_and_database_health_do_not_500():
    from dashboard import app

    client = TestClient(app)
    acc = client.get("/api/oracle/accuracy/public")
    dbh = client.get("/api/database/health")
    uni = client.get("/api/universe/status")
    assert acc.status_code == 200
    assert dbh.status_code == 200
    assert uni.status_code == 200
    assert dbh.json().get("engine") in {"sqlite", "postgresql"}
