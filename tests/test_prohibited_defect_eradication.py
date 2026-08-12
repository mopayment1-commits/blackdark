"""Permanent regression gates for prohibited defect classes."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_no_default_on_enterprise_sso_demo():
    src = (ROOT / "enterprise_sso.py").read_text(encoding="utf-8")
    assert 'ENTERPRISE_SSO_DEMO", "false"' in src or "ENTERPRISE_SSO_DEMO', 'false'" in src
    assert 'ENTERPRISE_SSO_DEMO", "true"' not in src


def test_scim_ready_is_true_with_real_module():
    from scim_service import scim_ready, scim_status

    assert scim_ready() is True
    assert scim_status()["product_complete"] is True


def test_unknown_fee_never_becomes_zero():
    from fee_matrix import taker_fee, withdrawal_fee_usdt

    assert taker_fee("totally_unknown_venue_xyz") is None
    assert withdrawal_fee_usdt("totally_unknown_venue_xyz", "BTC/USDT") is None


def test_funding_zero_slippage_not_executable_without_depth():
    import config
    from arbitrage_engine import calculate_funding_arbitrage

    symbol = config.perpetual_symbols()[0]
    venues = list(config.enabled_exchanges())[:2]
    rates = {
        venues[0]: {symbol: {"funding_rate": 0.002}},
        venues[1]: {symbol: {"funding_rate": -0.001}},
    }
    assert calculate_funding_arbitrage(rates, quote_amount=1000) == []


def test_stale_as_live_forbidden():
    from streaming_institutional import prove_stale_cannot_be_live
    import time

    out = prove_stale_cannot_be_live(int(time.time() * 1000) - 60_000)
    assert out["blocked"] is True


def test_cex_dex_executor_blocks_indicative():
    import asyncio
    from bd_platform.cex_dex_executor import execute_cex_dex_opportunity

    async def _run():
        return await execute_cex_dex_opportunity(
            {
                "executable": False,
                "indicative": True,
                "asset": "BTC",
                "quote_usd": 100,
                "net_spread_bps": 50,
            },
            dry_run=True,
        )

    out = asyncio.run(_run())
    assert out["blocked"] is True
    assert out["reason"] == "not_executable"


def test_confidence_heuristic_not_probability():
    from confidence_truth import claim_heuristic

    d = claim_heuristic(0.91).to_dict()
    assert d["is_probability"] is False
    assert d["confidence_type"] == "heuristic_score"


def test_production_soft_launch_institutional_force_off(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("INSTITUTIONAL_LAUNCH", "true")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("VIRAL_MODE", "false")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "institutional-test-master-key-32b!!")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "institutional-test-pepper-32bytes!!")
    monkeypatch.setenv("ADMIN_API_KEY", "admin-test-key")
    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["soft_launch"] is False


def test_universe_100_platforms_105_assets():
    import config

    assert len(config.UNIVERSE_ASSETS) >= 105
    assert len(config.SYMBOLS) >= 105
    assert len(config.enabled_exchanges()) >= 100


def test_no_bd_saml_authn_stub_claimed_complete():
    # AuthnRequest may exist as real SAMLRequest encoding, but BD_SAML_AUTHN_ stub string must be gone.
    src = (ROOT / "enterprise_sso.py").read_text(encoding="utf-8")
    assert "BD_SAML_AUTHN_" not in src


def test_canonical_adoption_required_marker():
    src = (ROOT / "arbitrage_engine.py").read_text(encoding="utf-8")
    assert "adopt_order_books" in src
    assert "adopt_funding_rates" in src


def test_plan_audit_zero_partials():
    import plan_audit
    from collections import Counter

    c = Counter(r[2] for r in plan_audit._PLAN_ROWS)
    assert c.get("partial", 0) == 0
    assert c.get("planned", 0) == 0
    assert c["complete"] == len(plan_audit._PLAN_ROWS)
