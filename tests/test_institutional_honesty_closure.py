"""Institutional honesty gates — SSO claims, Soft Launch, Sonar baseline, JWKS."""

from __future__ import annotations

import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]


def test_sso_status_never_claims_default_demo():
    from enterprise_sso import sso_status

    st = sso_status()
    assert st["scim_ready"] is True
    assert st["demo_mode_default"] is False
    assert st.get("demo_mode_enabled") is False
    assert st["jwks_verification"] is True
    assert st["saml_verification"] is True


def test_sso_live_ready_requires_client_secret(monkeypatch):
    from enterprise_sso import configure_provider, sso_status
    from org_tenant import create_org

    monkeypatch.delenv("ENTERPRISE_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("ENTERPRISE_OIDC_CLIENT_ID", raising=False)
    monkeypatch.delenv("ENTERPRISE_OIDC_CLIENT_SECRET", raising=False)
    org = create_org(name="Live SSO", owner_email="live.owner@dd.example")
    row = configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://idp.example.com",
        client_id="client",
        client_secret="super-secret-client",
        authorize_url="https://idp.example.com/oauth2/v1/authorize",
        token_url="https://idp.example.com/oauth2/v1/token",
        jwks_uri="https://idp.example.com/jwks",
    )
    assert row["institutional_complete"] is True
    assert row["scim_ready"] is True
    assert sso_status(org["org_id"])["product_complete"] is True


def test_institutional_launch_forces_soft_launch_off(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("INSTITUTIONAL_LAUNCH", "true")
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "institutional-test-master-key-32b!!")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "institutional-test-pepper-32bytes!!")
    monkeypatch.setenv("ADMIN_API_KEY", "admin-test-key")
    monkeypatch.setenv("VIRAL_MODE", "false")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["institutional_launch"] is True
    assert report["soft_launch"] is False
    ids = {c["id"]: c for c in report["checks"]}
    assert ids["institutional_soft_launch_unset"]["ok"] is True
    assert ids["enterprise_sso_demo_off"]["ok"] is True


def test_sonar_post_baseline_version_increment():
    ver = (ROOT / "SONAR_PROJECT_VERSION").read_text(encoding="utf-8").strip()
    assert ver == "2026.08.12.1"
    props = (ROOT / "sonar-project.properties").read_text(encoding="utf-8")
    assert "sonar.projectVersion=2026.08.12.1" in props


def test_sso_saml_authorize_requires_cert_for_complete(monkeypatch):
    from enterprise_sso import build_sso_authorize_url, configure_provider
    from org_tenant import create_org

    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    org = create_org(name="SAML Org", owner_email="saml.owner@dd.example")
    row = configure_provider(
        org["org_id"],
        protocol="saml",
        issuer="https://idp.example.com",
        client_id="saml-client",
        client_secret="secret",
        metadata_url="https://idp.example.com/metadata",
        authorize_url="https://idp.example.com/sso",
    )
    assert row["institutional_complete"] is False  # no IdP cert yet
    assert row["scim_ready"] is True
    auth = build_sso_authorize_url(
        org["org_id"],
        redirect_uri="http://127.0.0.1:8080/callback",
        email_hint="u@dd.example",
    )
    assert auth["ready"] is True
    assert auth["protocol"] == "saml"
    assert auth["institutional_complete"] is False
    assert "SAMLRequest" in auth["authorize_url"]


def test_sso_live_callback_with_jwks_id_token(monkeypatch):
    import asyncio

    from enterprise_sso import build_sso_authorize_url, complete_sso_login_async, configure_provider
    from org_tenant import create_org

    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key()

    class _Key:
        key = pub

    class _Client:
        def get_signing_key_from_jwt(self, _token):
            return _Key()

    monkeypatch.setattr("oidc_jwks_verify._client_for", lambda uri: _Client())

    org = create_org(name="Live CB", owner_email="livecb.owner@dd.example")
    configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://idp.example.com",
        client_id="client",
        client_secret="super-secret-client",
        authorize_url="https://idp.example.com/oauth2/v1/authorize",
        token_url="https://idp.example.com/oauth2/v1/token",
        jwks_uri="https://idp.example.com/jwks",
        audiences=["client"],
    )
    auth = build_sso_authorize_url(
        org["org_id"],
        redirect_uri="http://127.0.0.1:8080/callback",
        email_hint="live.user@dd.example",
    )
    assert auth["institutional_complete"] is True
    now = int(time.time())
    id_token = jwt.encode(
        {
            "iss": "https://idp.example.com",
            "aud": "client",
            "sub": "sub-1",
            "email": "live.user@dd.example",
            "iat": now,
            "nbf": now - 5,
            "exp": now + 300,
            "nonce": auth["nonce"],
        },
        key,
        algorithm="RS256",
        headers={"kid": "k1"},
    )

    async def _run():
        import database

        await database.init_db()
        return await complete_sso_login_async(state=auth["state"], id_token=id_token)

    result = asyncio.run(_run())
    assert result["demo_or_live"] == "live"
    assert result["crypto_verified"] is True
    assert result["product_complete"] is True
    assert result["institutional_complete"] is True
    assert result["scim_ready"] is True


def test_sso_env_oidc_authorize_fallback(monkeypatch):
    from enterprise_sso import build_sso_authorize_url
    from org_tenant import create_org

    org = create_org(name="Env SSO", owner_email="env.owner@dd.example")
    monkeypatch.setenv("ENTERPRISE_OIDC_ISSUER", "https://okta.example.com")
    monkeypatch.setenv("ENTERPRISE_OIDC_CLIENT_ID", "env-client")
    monkeypatch.setenv("ENTERPRISE_OIDC_CLIENT_SECRET", "env-secret")
    monkeypatch.setenv("ENTERPRISE_OIDC_AUTHORIZE_URL", "https://okta.example.com/oauth2/v1/authorize")
    auth = build_sso_authorize_url(
        org["org_id"],
        redirect_uri="http://127.0.0.1:8080/callback",
        email_hint="env.user@dd.example",
    )
    assert auth["ready"] is True
    assert "env-client" in auth["authorize_url"]


def test_institutional_blocks_sso_demo(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("INSTITUTIONAL_LAUNCH", "true")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "true")
    monkeypatch.setenv("VIRAL_MODE", "false")
    monkeypatch.setenv("SERVICE_MODE", "web")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    ids = {c["id"]: c for c in report["checks"]}
    assert report["soft_launch"] is False
    assert ids["enterprise_sso_demo_off"]["ok"] is False
    assert "enterprise_sso_demo_off" in report["required_failures"]


def test_raw_code_without_jwt_fails_closed(monkeypatch):
    import asyncio

    from enterprise_sso import build_sso_authorize_url, complete_sso_login_async, configure_provider
    from org_tenant import create_org

    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    org = create_org(name="No JWT", owner_email="nojwt@dd.example")
    configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://idp.example.com",
        client_id="client",
        client_secret="secret",
        authorize_url="https://idp.example.com/auth",
        jwks_uri="https://idp.example.com/jwks",
    )
    auth = build_sso_authorize_url(org["org_id"], redirect_uri="http://127.0.0.1/cb")

    async def _run():
        with pytest.raises(ValueError, match="oidc_id_token_required"):
            await complete_sso_login_async(state=auth["state"], code="not-a-jwt")

    asyncio.run(_run())
