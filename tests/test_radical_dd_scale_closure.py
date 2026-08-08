"""Radical DD + scale closure tests."""

from __future__ import annotations

import os

import pytest


def test_stealth_advisor_uses_advisory_slice_labels():
    from stealth_execution_advisor import advise_stealth_execution

    small = advise_stealth_execution(asset="BTC", notional_usd=1_000)
    assert small["slice_plan"]["algo"] == "LIMIT_CLIP_ADVISORY"
    assert "TWAP" not in small["slice_plan"]["algo"] or "SLICE_" in small["slice_plan"]["algo"]

    large = advise_stealth_execution(asset="BTC", notional_usd=50_000_000)
    algo = large["slice_plan"]["algo"]
    assert algo in {"SLICE_TWAP_STYLE", "SLICE_VWAP_STYLE", "LIMIT_CLIP_ADVISORY"}
    assert algo != "TWAP"
    assert algo != "VWAP_lite"


def test_execution_risk_score_band():
    from execution_risk_score import score_execution_risk

    low = score_execution_risk(
        {
            "total_slippage_bps": 5,
            "data_age_sec": 0.2,
            "execution_feasibility": "high",
            "net_profit_usdt": 20,
            "confidence_percent": 80,
        }
    )
    assert low["execution_risk_pct"] < 25
    assert low["execution_risk_band"] == "low"

    high = score_execution_risk(
        {
            "total_slippage_bps": 120,
            "data_age_sec": 40,
            "execution_feasibility": "low",
            "net_profit_usdt": -1,
            "risk_factors": ["a", "b", "c"],
            "confidence_percent": 20,
        }
    )
    assert high["execution_risk_pct"] >= 75


def test_freshness_chip_states():
    from data_freshness import freshness_chip

    assert freshness_chip(freshness_ms=500)["state"] == "fresh"
    assert freshness_chip(age_sec=5)["state"] == "ok"
    assert freshness_chip(age_sec=40)["state"] == "stale"


def test_audience_progressive_disclosure():
    from audience_routing import audience_entry

    retail = audience_entry("retail")
    assert retail["progressive_disclosure"]["shell"] == "oracle_first"
    whale = audience_entry("whale")
    assert "stealth" in whale["progressive_disclosure"]["emphasize"]


def test_scale_readiness_honesty(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.delenv("REDIS_URL", raising=False)
    from scale_readiness import scale_readiness_report

    report = scale_readiness_report()
    assert report["capacity_claim"]["proven_high_concurrency_signed"] is False
    assert "LOAD_TEST_RUN_LOG" in report["capacity_claim"]["proof_path"]


def test_production_guard_rejects_insecure_defaults(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "blackdark-dev-change-me-in-production")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "blackdark-session-pepper-change-me")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("ADMIN_API_KEY", "x")
    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "no_insecure_prod_secret_defaults" in report["required_failures"]


def test_mfa_totp_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-mfa-key-not-for-prod-32b!")
    import pyotp

    from mfa_service import generate_totp_secret, verify_totp

    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code) is True
    assert verify_totp(secret, "000000") is False


def test_oauth_status_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GITHUB_CLIENT_ID", raising=False)
    from oauth_service import oauth_status

    status = oauth_status()
    assert status["enabled"] is False


def test_trust_os_mfa_claim_not_naked():
    from trust_os import trust_os_manifest

    manifest = trust_os_manifest()
    inst = next(layer for layer in manifest["value_layers"] if layer["id"] == "institutional_packaging")
    joined = " ".join(inst["capabilities"] + inst.get("honest_limits", []))
    assert "MFA" in joined
    assert "not a compliance certificate" in " ".join(inst.get("honest_limits", [])).lower() or \
        "engineering" in " ".join(inst.get("honest_limits", [])).lower()


def test_data_room_doc_exists():
    assert os.path.isfile("docs/DATA_ROOM.md")
    assert os.path.isfile("deploy/k8s/workers-deployment.yaml")
    assert os.path.isfile("alembic/versions/20260808_0001_baseline_mfa_oauth.py")


@pytest.mark.asyncio
async def test_compliance_and_scale_routes():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/compliance")
        assert r.status_code == 200
        assert "Anti-Hype" in r.text or "Compliance" in r.text

        r2 = await client.get("/data-room")
        assert r2.status_code == 200

        r3 = await client.get("/api/scale/readiness")
        assert r3.status_code == 200
        body = r3.json()
        assert body["capacity_claim"]["proven_high_concurrency_signed"] is False

        r4 = await client.get("/api/auth/oauth/status")
        assert r4.status_code == 200
