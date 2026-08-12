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


def test_scim_ready_requires_bearer(monkeypatch):
    monkeypatch.delenv("SCIM_BEARER_TOKEN", raising=False)
    from importlib import reload
    import scim_service
    reload(scim_service)
    assert scim_service.scim_ready() is False
    monkeypatch.setenv("SCIM_BEARER_TOKEN", "test-scim-bearer-token")
    reload(scim_service)
    assert scim_service.scim_ready() is True
    assert scim_service.scim_status()["product_complete"] is True


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


def test_cex_dex_unknown_fee_never_executable():
    from bd_platform.cex_dex_arbitrage import _cex_dex_row

    row = _cex_dex_row(
        "BTC",
        {"binance": 100.0},
        100.0,
        {"price": 99.0, "venue": "jupiter", "liquidity_usd": 10_000_000.0},
        "jupiter",
        99.0,
        "binance",
        100.0,
        100.0,
        80.0,
        1000.0,
        # default fee_bps=None must not invent free fees
        cex_l2_walk_verified=True,
    )
    assert row["executable"] is False
    assert row["fees_known"] is False
    assert row["indicative_reason"] == "fee_unknown"
    assert row["estimated_profit_usd"] is None


def test_funding_helper_never_returns_zero_slip_when_missing():
    from arbitrage_engine import _funding_depth_slippage_bps

    slip, ok, reason = _funding_depth_slippage_bps(
        None, symbol="BTC/USDT", long_exchange="binance", short_exchange="okx", notional=1000
    )
    assert slip is None
    assert ok is False
    assert reason == "order_books_missing"


def test_coverage_percent_is_live_not_catalog():
    import asyncio
    from platform_universe import compute_universe_coverage

    cov = asyncio.run(compute_universe_coverage())
    assert cov["coverage_percent_exchanges"] == cov["live_coverage_percent_exchanges"]
    assert "catalog_ready_percent_exchanges" in cov
    assert "catalog_ready ≠ live" in cov["honesty"]
    # Vanity inflation gate: live percent must equal live sources / target
    target = max(cov["target"]["exchanges"], 1)
    expected = round(cov["live_ingestion_sources"] / target * 100, 1)
    assert cov["coverage_percent_exchanges"] == expected


def test_plan_audit_honest_catalog_partial_allowed():
    import plan_audit
    from collections import Counter

    c = Counter(r[2] for r in plan_audit._PLAN_ROWS)
    # Catalog honesty: planned/proxy mix may be partial — never invent 46/46 complete.
    assert c.get("planned", 0) == 0
    assert c["complete"] + c.get("partial", 0) == len(plan_audit._PLAN_ROWS)
    catalog = [r for r in plan_audit._PLAN_ROWS if "77 arbitrage" in r[1]]
    assert catalog and catalog[0][2] == "partial"


def test_cex_dex_requires_gas_and_l2_for_executable():
    from bd_platform.cex_dex_arbitrage import _cex_dex_row
    from live_book_hub import update_top_of_book

    update_top_of_book("binance", "BTC/USDT", bid=99.0, bid_qty=100.0, ask=100.0, ask_qty=100.0)
    # fee known but gas missing → not executable
    row = _cex_dex_row(
        "BTC", {"binance": 100.0}, 100.0,
        {"price": 99.0, "venue": "jupiter", "liquidity_usd": 10_000_000.0},
        "binance", 100.0, "jupiter", 99.0, 100.0, 80.0, 1000.0,
        fee_bps=10.0, cex_l2_walk_verified=True,
    )
    assert row["executable"] is False
    assert row["indicative_reason"] == "gas_unknown"
    row2 = _cex_dex_row(
        "BTC", {"binance": 100.0}, 100.0,
        {"price": 99.0, "venue": "jupiter", "liquidity_usd": 10_000_000.0},
        "binance", 100.0, "jupiter", 99.0, 100.0, 80.0, 1000.0,
        fee_bps=10.0, cex_l2_walk_verified=True, gas_bps=35.0,
    )
    assert row2["executable"] is True
    assert row2["gas_known"] is True


def test_correlation_contagion_fail_closed_high_concentration():
    from risk_intelligence import correlation_contagion_risk
    out = correlation_contagion_risk(positions=[
        {"asset": "BTC", "notional_usd": 900_000},
        {"asset": "ETH", "notional_usd": 50_000},
        {"asset": "SOL", "notional_usd": 50_000},
    ])
    assert out["executable"] is False
    assert out["gate"] == "block"
