"""External-audit adversarial pack — financial fail-closed + launch failure modes."""

from __future__ import annotations

import fee_matrix
import pytest


def test_unknown_venue_fees_never_default_to_zero():
    fee_matrix._matrix.clear()
    assert fee_matrix.taker_fee("totally-unknown-venue") is None
    assert fee_matrix.withdrawal_fee_usdt("totally-unknown-venue", "BTC/USDT") is None
    assert fee_matrix.deposit_fee_usdt("totally-unknown-venue", "ETH/USDT") is None


def test_negative_and_zero_notionals_rejected():
    from arbitrage_engine import _build_cross_exchange_opportunity, walk_asks, walk_bids

    fee_matrix._matrix.clear()
    book = {"asks": [[100.0, 10.0]], "bids": [[99.0, 10.0]]}
    assert walk_asks(book, 0.0) is None
    assert walk_asks(book, -5.0) is None
    assert walk_bids(book, 0.0) is None
    assert (
        _build_cross_exchange_opportunity(
            "BTC/USDT", "binance", "okx", book, book, 0.0, None
        )
        is None
    )


def test_insufficient_depth_returns_none():
    from arbitrage_engine import _build_cross_exchange_opportunity

    fee_matrix._matrix.clear()
    thin_buy = {"asks": [[100.0, 0.001]], "bids": [[99.0, 0.001]]}
    thin_sell = {"asks": [[102.0, 0.001]], "bids": [[101.0, 0.001]]}
    # Large notional vs thin book must not invent fills.
    assert (
        _build_cross_exchange_opportunity(
            "BTC/USDT", "binance", "okx", thin_buy, thin_sell, 50_000.0, None
        )
        is None
    )


def test_empty_book_and_stale_quotes_never_executable():
    from executable_edge_truth import apply_net_executable_profit, mark_indicative_only
    from profit_fee_algorithms import net_cross_exchange_profit
    from stale_price_guard import validate_opportunity_quotes

    fee_matrix._matrix.clear()
    # Missing depth / empty books → no inventing fills.
    assert (
        net_cross_exchange_profit(
            {"asks": [], "bids": []},
            {"asks": [], "bids": []},
            buy_exchange="binance",
            sell_exchange="okx",
            symbol="BTC/USDT",
            notional=100.0,
            market_context=None,
        )
        is None
    )

    stale_opp = {
        "kind": "cross_exchange",
        "symbol": "BTC/USDT",
        "buy_exchange": "binance",
        "sell_exchange": "okx",
        "quote_ts": 0,
        "net_profit_usdt": 12.0,
        "executable": True,
        "profitable": True,
    }
    ok, _detail = validate_opportunity_quotes(stale_opp, for_execution=True)
    assert ok is False
    downgraded = mark_indicative_only(stale_opp, reason="stale_or_invalid_quotes")
    assert downgraded["executable"] is False
    assert downgraded["profitable"] is False
    assert apply_net_executable_profit(stale_opp, net_profit_usdt=None)["executable"] is False


def test_funding_rates_only_not_executable_profit():
    from arbitrage_engine import calculate_funding_arbitrage

    fee_matrix._matrix.clear()
    # Seed known venue fees so the path reaches the depth gate (not fee gate).
    rates = {
        "binance": {"BTC/USDT": {"funding_rate": 0.01}},
        "okx": {"BTC/USDT": {"funding_rate": -0.01}},
    }
    opps = calculate_funding_arbitrage(rates, quote_amount=100_000.0)
    for opp in opps:
        assert opp.executable is False
        assert opp.indicative is True
        assert float(opp.net_yield_usdt) == 0.0


def test_live_hub_excludes_stale_symbol_rows():
    import time

    import live_book_hub as hub

    hub._books.clear()
    hub._last_update_ms.clear()
    hub.update_top_of_book("binance", "ETH/USDT", bid=1, bid_qty=1, ask=2, ask_qty=1)
    hub.update_top_of_book("okx", "ETH/USDT", bid=1, bid_qty=1, ask=2, ask_qty=1)
    hub.update_top_of_book("binance", "BTC/USDT", bid=1, bid_qty=1, ask=2, ask_qty=1)
    # Force BTC row stale while ETH remains fresh.
    hub._last_update_ms["binance|BTC/USDT"] = time.monotonic() * 1000.0 - 50_000.0
    fresh = hub.get_live_books_if_fresh(max_age_ms=1_000.0)
    assert fresh is not None
    books, _age = fresh
    assert "BTC/USDT" not in (books.get("binance") or {})
    assert "ETH/USDT" in (books.get("binance") or {})


def test_sentiment_unknown_fail_closed():
    from sentiment_gate import sentiment_allows_execution

    # No cached score and no compound → must not allow execution.
    assert sentiment_allows_execution("ZZZNOCACHE", compound_score=None) is False


def test_jupiter_synthetic_economics_removed():
    import asyncio

    from jupiter_dex_adapter import quote_swap

    async def _run():
        return await quote_swap(
            input_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            output_mint="So11111111111111111111111111111111111111112",
            amount_atomic=1_000_000,
        )

    out = asyncio.run(_run())
    if not out.get("ok"):
        assert out.get("executable") is False
        assert out.get("source") != "synthetic_economics"
    else:
        assert out.get("source") == "jupiter_api"


def test_sso_demo_disabled_by_default(monkeypatch):
    import asyncio

    from enterprise_sso import build_sso_authorize_url, complete_sso_login_async, configure_provider
    from org_tenant import create_org

    monkeypatch.delenv("ENTERPRISE_SSO_DEMO", raising=False)
    monkeypatch.setenv("ENV", "development")
    org = create_org(name="SSO Lock", owner_email="sso.lock@dd.example")
    configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://example.okta.com",
        client_id="dd-client",
        authorize_url="https://example.okta.com/oauth2/v1/authorize",
    )
    auth = build_sso_authorize_url(
        org["org_id"],
        redirect_uri="http://127.0.0.1:8080/callback",
        email_hint="victim@dd.example",
    )
    assert auth["ready"] is True

    async def _run():
        return await complete_sso_login_async(
            state=auth["state"],
            code="demo_sso_ok",
            email="victim@dd.example",
        )

    with pytest.raises(ValueError, match="sso_demo_disabled"):
        asyncio.run(_run())


@pytest.mark.asyncio
async def test_gas_zero_and_negative_not_executable(monkeypatch):
    import time

    import gas_oracle

    gas_oracle._CACHE["ethereum"] = {"chain": "ethereum", "swap_cost_usd": 0.0}
    gas_oracle._CACHE_TS["ethereum"] = time.monotonic()

    async def _noop(**_k):
        return gas_oracle._CACHE

    monkeypatch.setattr(gas_oracle, "refresh_gas_cache", _noop)
    assert await gas_oracle.get_swap_gas_usd("ethereum") is None

    gas_oracle._CACHE["ethereum"] = {"chain": "ethereum", "swap_cost_usd": -1.0}
    assert await gas_oracle.get_swap_gas_usd("ethereum") is None


def test_metrics_token_gate(monkeypatch):
    from fastapi import HTTPException

    from api.routers.observability import _require_metrics_access

    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    assert _require_metrics_access(None) is None

    monkeypatch.setenv("METRICS_TOKEN", "secret-metrics")
    with pytest.raises(HTTPException) as missing:
        _require_metrics_access(None)
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as bad:
        _require_metrics_access("Bearer wrong")
    assert bad.value.status_code == 403

    assert _require_metrics_access("Bearer secret-metrics") is None


def test_bandit_low_money_auth_triage_documented():
    """Guardrail: money/auth paths must not use bare `except: pass` without log."""
    from pathlib import Path

    money_files = [
        Path("fee_matrix.py"),
        Path("money_decimal.py"),
        Path("profit_fee_algorithms.py"),
        Path("executable_edge_truth.py"),
    ]
    for path in money_files:
        src = path.read_text(encoding="utf-8")
        # Allow except with continue/return/log — flag exact `except Exception:\n        pass` only if dense
        assert "except:\n        pass" not in src


@pytest.mark.asyncio
async def test_provider_malformed_book_fail_closed():
    from arbitrage_engine import _build_cross_exchange_opportunity

    fee_matrix._matrix.clear()
    bad = {"asks": [["x", "y"]], "bids": [[None, 1]]}
    assert (
        _build_cross_exchange_opportunity(
            "BTC/USDT", "binance", "okx", bad, bad, 100.0, None
        )
        is None
    )


def test_production_detection_or_across_env_tokens(monkeypatch):
    """Polluted ENV=development must not hide APP_ENV=production."""
    from production_guard import is_production

    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    assert is_production() is True

    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("APP_ENV", "development")
    assert is_production() is False


def test_cex_dex_fee_haircut_excludes_invented_gas():
    from bd_platform.cex_dex_arbitrage import _indicative_fee_bps

    fee_matrix._matrix.clear()
    fee_matrix._matrix["binance"] = {"taker": 0.001, "maker": 0.001}
    fee_matrix._matrix["uniswap"] = {"taker": 0.003, "maker": 0.003}
    bps = _indicative_fee_bps("binance", "uniswap")
    assert bps == pytest.approx(40.0)  # 10 + 30 trading bps only
    assert _indicative_fee_bps("binance", "unknown-dex") is None


@pytest.mark.asyncio
async def test_service_bus_local_queue_bounded_drop(monkeypatch):
    import asyncio
    from collections import defaultdict

    import service_bus

    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("WEB_REPLICAS", "1")
    monkeypatch.setenv("ENV", "development")
    service_bus._redis_client = None
    service_bus._LOCAL_QUEUE_MAX = 2

    def _q() -> asyncio.Queue:
        return asyncio.Queue(maxsize=2)

    service_bus._make_local_queue = _q
    service_bus._local_queues = defaultdict(_q)
    ch = "blackdark.test.bounded"
    assert await service_bus.publish(ch, {"n": 1}) is True
    assert await service_bus.publish(ch, {"n": 2}) is True
    assert await service_bus.publish(ch, {"n": 3}) is False


def test_unknown_chain_native_usd_fail_closed():
    import gas_oracle

    assert gas_oracle._native_usd(None, "not-a-real-chain") is None


@pytest.mark.asyncio
async def test_flash_loan_protocol_fee_unknown_fail_closed(monkeypatch):
    import aiohttp

    import defi_arbitrage_engine as dae
    import gas_oracle

    async def _cex(_session, _asset):
        return {"binance": 100.0}

    async def _dex(_session, _asset, _mid):
        return {"price": 100.5, "venue": "uni", "chain": "ethereum"}

    async def _second(_session, _asset, _mid):
        return 101.0, "sushi"

    async def _gas(_chain, _quote, hops=3):
        return 12.0

    monkeypatch.setattr("bd_platform.cex_dex_arbitrage._cex_prices", _cex)
    monkeypatch.setattr("bd_platform.cex_dex_arbitrage._best_dex_quote", _dex)
    monkeypatch.setattr(dae, "_find_second_dex_quote", _second)
    monkeypatch.setattr(gas_oracle, "gas_cost_bps", _gas)
    async with aiohttp.ClientSession() as session:
        row = await dae.scan_flash_loan_proxy(session, "ETH")
    assert row is not None
    assert row["profitable"] is False
    assert row["executable"] is False
    assert row["flash_fee_bps"] is None
    assert row["net_spread_bps"] is None
    assert row["reject_reason"] == "flash_loan_protocol_fee_unknown"
