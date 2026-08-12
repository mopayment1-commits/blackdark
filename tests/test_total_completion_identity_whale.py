"""Total completion gates — JWKS/OIDC, SAML, SCIM, whale, canonical adoption."""

from __future__ import annotations
import os
os.environ.setdefault("SCIM_BEARER_TOKEN", "test-scim-bearer-token")

import base64
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]


def _rsa_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key()
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "idp.test")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "idp.test")]))
        .public_key(pub)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    return key, priv_pem, cert_pem, pub


def _mint_id_token(priv_key, *, issuer, audience, email, nonce, exp_delta=300, kid="test-kid"):
    now = int(time.time())
    headers = {"kid": kid, "alg": "RS256"}
    claims = {
        "iss": issuer.rstrip("/"),
        "aud": audience,
        "sub": "user-1",
        "email": email,
        "iat": now,
        "exp": now + exp_delta,
        "nbf": now - 5,
        "nonce": nonce,
    }
    return jwt.encode(claims, priv_key, algorithm="RS256", headers=headers)


def test_oidc_jwks_verify_signature_iss_aud_exp(monkeypatch):
    from oidc_jwks_verify import OidcVerificationError, clear_jwks_cache, verify_id_token

    clear_jwks_cache()
    key, _, _, pub = _rsa_pair()
    issuer = "https://idp.example.com"
    aud = "client-1"
    token = _mint_id_token(key, issuer=issuer, audience=aud, email="a@b.com", nonce="n1")

    class _Key:
        key = pub

    class _Client:
        def get_signing_key_from_jwt(self, _token):
            return _Key()

    monkeypatch.setattr("oidc_jwks_verify._client_for", lambda uri: _Client())
    claims = verify_id_token(token, issuer=issuer, audience=aud, jwks_uri="https://idp.example.com/jwks", nonce="n1")
    assert claims["email"] == "a@b.com"

    with pytest.raises(OidcVerificationError):
        verify_id_token(token, issuer=issuer, audience="wrong", jwks_uri="https://x/jwks", nonce="n1")

    expired = _mint_id_token(key, issuer=issuer, audience=aud, email="a@b.com", nonce="n1", exp_delta=-120)
    with pytest.raises(OidcVerificationError):
        verify_id_token(expired, issuer=issuer, audience=aud, jwks_uri="https://x/jwks", nonce="n1", leeway_sec=0)

    # tampered
    bad = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(OidcVerificationError):
        verify_id_token(bad, issuer=issuer, audience=aud, jwks_uri="https://x/jwks", nonce="n1")


def test_saml_authn_and_response_verify():
    from saml_service import build_authn_request, build_test_response, verify_saml_response

    _, priv, cert, _ = _rsa_pair()
    req = build_authn_request(
        acs_url="https://app.example/acs",
        destination="https://idp.example/sso",
        issuer="blackdark:org1",
    )
    assert req["SAMLRequest"]
    assert "AuthnRequest" in req["xml"]

    audience = "blackdark:org1"
    dest = "https://app.example/acs"
    resp = build_test_response(
        email="saml.user@example.com",
        audience=audience,
        destination=dest,
        private_key_pem=priv,
    )
    out = verify_saml_response(
        saml_response_b64=resp,
        idp_cert_pem=cert,
        expected_audience=audience,
        expected_destination=dest,
    )
    assert out["verified"] is True
    assert out["email"] == "saml.user@example.com"


def test_scim_users_groups_roundtrip(tmp_path, monkeypatch):
    import scim_service as scim
    from org_tenant import create_org

    monkeypatch.setattr(scim, "_PATH", tmp_path / "scim_store.json")
    monkeypatch.setattr(scim, "_DATA_BASE", tmp_path)
    org = create_org(name="SCIM Org", owner_email="owner@scim.example")
    user = scim.create_user(
        org_id=org["org_id"],
        user_name="alice",
        email="alice@scim.example",
        role="analyst",
    )
    assert user["id"]
    listed = scim.list_users(org_id=org["org_id"], filter_expr='userName eq "alice"')
    assert listed["totalResults"] == 1
    patched = scim.patch_user(user["id"], org_id=org["org_id"], operations=[{"op": "replace", "path": "active", "value": False}])
    assert patched["active"] is False
    group = scim.create_group(org_id=org["org_id"], display_name="Desk", members=[user["id"]])
    assert group["displayName"] == "Desk"
    assert scim.scim_status()["scim_ready"] is True


def test_enterprise_sso_oidc_requires_jwks_verified_token(monkeypatch, tmp_path):
    import asyncio

    import enterprise_sso as eso
    from org_tenant import create_org

    monkeypatch.setattr(eso, "_PATH", tmp_path / "enterprise_sso.json")
    monkeypatch.setattr(eso, "_DATA_BASE", tmp_path)
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    key, _, _, pub = _rsa_pair()

    class _Key:
        key = pub

    class _Client:
        def get_signing_key_from_jwt(self, _token):
            return _Key()

    monkeypatch.setattr("oidc_jwks_verify._client_for", lambda uri: _Client())

    org = create_org(name="OIDC Org", owner_email="owner@oidc.example")
    eso.configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://idp.example.com",
        client_id="client-1",
        client_secret="secret",
        authorize_url="https://idp.example.com/auth",
        jwks_uri="https://idp.example.com/jwks",
        audiences=["client-1"],
    )
    auth = eso.build_sso_authorize_url(
        org["org_id"],
        redirect_uri="https://app.example/cb",
        email_hint="live.user@oidc.example",
    )
    assert auth["institutional_complete"] is True
    token = _mint_id_token(
        key,
        issuer="https://idp.example.com",
        audience="client-1",
        email="live.user@oidc.example",
        nonce=auth["nonce"],
    )

    async def _run():
        import database

        await database.init_db()
        return await eso.complete_sso_login_async(state=auth["state"], id_token=token)

    result = asyncio.run(_run())
    assert result["crypto_verified"] is True
    assert result["product_complete"] is True
    assert result["scim_ready"] is True
    assert result["email"] == "live.user@oidc.example"


def test_enterprise_sso_saml_crypto_path(monkeypatch, tmp_path):
    import asyncio

    import enterprise_sso as eso
    from org_tenant import create_org
    from saml_service import build_test_response

    monkeypatch.setattr(eso, "_PATH", tmp_path / "enterprise_sso.json")
    monkeypatch.setattr(eso, "_DATA_BASE", tmp_path)
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    _, priv, cert, _ = _rsa_pair()
    org = create_org(name="SAML Org", owner_email="owner@saml.example")
    eso.configure_provider(
        org["org_id"],
        protocol="saml",
        issuer="https://idp.example.com",
        client_id="saml",
        authorize_url="https://idp.example.com/sso",
        idp_cert_pem=cert,
    )
    auth = eso.build_sso_authorize_url(
        org["org_id"],
        redirect_uri="https://app.example/acs",
        email_hint="u@saml.example",
    )
    assert auth["protocol"] == "saml"
    assert auth["institutional_complete"] is True
    assert "SAMLRequest=" in auth["authorize_url"]
    resp = build_test_response(
        email="u@saml.example",
        audience=f"blackdark:{org['org_id']}",
        destination="https://app.example/acs",
        private_key_pem=priv,
    )

    async def _run():
        import database

        await database.init_db()
        return await eso.complete_sso_login_async(state=auth["state"], saml_response=resp)

    result = asyncio.run(_run())
    assert result["protocol"] == "saml"
    assert result["crypto_verified"] is True


def test_whale_evidence_measured(tmp_path, monkeypatch):
    import whale_execution_evidence as we

    monkeypatch.setattr(we, "_EVIDENCE", tmp_path / "whale_execution_evidence.jsonl")
    monkeypatch.setattr(we, "_DATA_BASE", tmp_path)

    def deep_book(mid=100.0):
        return {
            "bids": [[mid - i * 0.05, 5000.0] for i in range(1, 40)],
            "asks": [[mid + i * 0.05, 5000.0] for i in range(1, 40)],
        }

    books = {
        "binance": {"BTC/USDT": deep_book()},
        "okx": {"BTC/USDT": deep_book()},
        "bybit": {"BTC/USDT": deep_book()},
    }
    out = we.measure_whale_readiness(books, symbol="BTC/USDT")
    assert out["whale_ready"] is True
    assert out["product_complete"] is True
    assert out["probes"]


def test_canonical_adoption_on_cross_path():
    from arbitrage_engine import calculate_cross_exchange_arbitrage
    from canonical_data_layer import EntityType, get_datum, reset_store_for_tests

    reset_store_for_tests()
    books = {
        "OKEX": {
            "btcusdt": {
                "bids": [[100.0, 10.0]],
                "asks": [[101.0, 10.0]],
            }
        },
        "binance": {
            "BTC/USDT": {
                "bids": [[102.0, 10.0]],
                "asks": [[103.0, 10.0]],
            }
        },
    }
    # Should normalize without raising; may return [] if no executable edge
    calculate_cross_exchange_arbitrage(books, quote_amount=100.0)
    assert get_datum(EntityType.ORDER_BOOK, "okx:BTC/USDT") is not None


def test_scim_http_ready(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "scim-ready-admin")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    from fastapi.testclient import TestClient

    from dashboard import app
    from org_tenant import create_org

    org = create_org(name="HTTP SCIM", owner_email="h@scim.example")
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-scim-bearer-token", "X-Admin-Key": "scim-ready-admin"}
    st = client.get("/api/institutional/scim/status", headers=headers)
    # status does not require SCIM bearer
    assert st.status_code == 200
    assert st.json()["scim_ready"] is True
    created = client.post(
        "/api/institutional/scim/v2/Users",
        headers=headers,
        json={
            "userName": "bob",
            "emails": [{"value": "bob@scim.example"}],
            "urn:blackdark:params:scim:schemas:extension:tenant:2.0:User": {
                "org_id": org["org_id"],
                "role": "viewer",
            },
        },
    )
    assert created.status_code == 200
    assert created.json()["userName"] == "bob"


def test_continuous_learning_and_white_label(tmp_path, monkeypatch):
    import continuous_learning as cl
    import white_label as wl

    monkeypatch.setattr(cl, "_PATH", tmp_path / "continuous_learning.jsonl")
    monkeypatch.setattr(cl, "_DATA_BASE", tmp_path)
    monkeypatch.setattr(wl, "_PATH", tmp_path / "white_label.json")
    monkeypatch.setattr(wl, "_DATA_BASE", tmp_path)

    with pytest.raises(ValueError, match="look_ahead"):
        cl.record_outcome_evaluation(
            graph_id="g1",
            decision_node_id="d1",
            predicted={"label": "up"},
            actual={"label": "up"},
            decision_ts="2026-08-12T12:00:00+00:00",
            outcome_ts="2026-08-12T11:00:00+00:00",
        )
    cl.record_outcome_evaluation(
        graph_id="g1",
        decision_node_id="d1",
        predicted={"label": "up"},
        actual={"label": "up"},
        decision_ts="2026-08-12T12:00:00+00:00",
        outcome_ts="2026-08-12T13:00:00+00:00",
    )
    assert cl.calibrate_from_history(min_samples=30)["confidence_type"] == "insufficient_evidence"

    brand = wl.configure_brand(org_id="orgx", product_name="Acme Desk", report_footer="Acme only")
    assert brand["product_name"] == "Acme Desk"
    export = wl.branded_report_export("orgx", {"pnl": 1})
    assert "Acme" in export["footer"]


def test_flash_crash_and_microstructure():
    from flash_crash_protection import detect_flash_crash
    from microstructure_intelligence import liquidity_intelligence, order_book_microstructure

    m = order_book_microstructure(
        {"bids": [[100, 50], [99, 50]], "asks": [[100.2, 50], [100.5, 50]]},
        notional=1000,
    )
    assert m["spread_bps"] > 0
    liq = liquidity_intelligence(
        {
            "binance": {"bids": [[100, 200]], "asks": [[100.1, 200]]},
            "okx": {"bids": [[100, 200]], "asks": [[100.1, 200]]},
        },
        notional=500,
    )
    assert liq["exitability"] is True
    crash = detect_flash_crash(
        returns_bps=[-900],
        window_sec=30,
        spread_bps_now=80,
        spread_bps_baseline=10,
        depth_now=100,
        depth_baseline=1000,
        venue_mids={"binance": 100, "okx": 101},
    )
    assert crash["gate"] == "block"
    assert "price_velocity" in crash["signals"]


def test_oms_cancel_replace(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    import oms

    monkeypatch.setattr(oms, "_PATH", tmp_path / "oms.json")
    monkeypatch.setattr(oms, "_DATA_BASE", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "oms_cancel_replace.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    order = oms.create_intent(
        org_id="o1",
        venue="binance",
        symbol="BTC/USDT",
        side="buy",
        quantity=1,
        idempotency_key="cr1",
        actor="t",
        limit_price=100,
    )
    oms.transition(order["order_id"], "VALIDATION", actor="t")
    oms.transition(order["order_id"], "RISK_CHECK", actor="t")
    oms.transition(order["order_id"], "ROUTING", actor="t")
    oms.transition(order["order_id"], "SUBMISSION", actor="t")
    oms.transition(order["order_id"], "ACK", actor="t")
    repl = oms.cancel_replace(order["order_id"], actor="t", new_limit_price=99.5)
    assert repl["replaces_order_id"] == order["order_id"]
    assert oms.get_order(order["order_id"])["state"] == "CANCEL"
