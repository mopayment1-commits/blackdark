"""Institutional honesty gates — SSO claims, Soft Launch, Sonar baseline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sso_status_never_claims_scim_or_default_demo():
    from enterprise_sso import sso_status

    st = sso_status()
    assert st["scim_ready"] is False
    assert st["demo_mode_default"] is False
    assert st.get("demo_mode_enabled") is False


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
    )
    assert row["institutional_complete"] is True
    assert row["scim_ready"] is False
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
    # Do not set a fake DATABASE_URL — institutional mode only asserts Soft Launch is forced off.

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
