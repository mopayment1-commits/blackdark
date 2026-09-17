"""Launch-57 Phase 1 Data Batch 1 — runtime and semantic contract tests."""

from __future__ import annotations

import pytest

from launch57.data_batch1 import (
    LAUNCH57_BATCH1_CAP_IDS,
    execute_launch57_batch1,
    ohlcv,
    real_time_prices,
    spot_market_metrics_suite,
    symbol_metadata,
    unified_exchange_connector,
    validate_ohlcv_invariants,
)


@pytest.mark.asyncio
async def test_unified_exchange_connector_routes_without_synthetic(monkeypatch):
    async def fake_probe(symbol: str = "BTC"):
        return {
            "symbol": symbol,
            "checks": {
                "api.binance.com": {"ok": True, "source": "binance:api.binance.com"},
                "kraken": {"ok": False},
            },
            "resolved": True,
            "resolved_source": "binance:api.binance.com",
        }

    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)
    out = await unified_exchange_connector(symbol="BTC", params={})
    assert out["capability_id"] == 504
    assert out["success"] is True
    assert out["selected_provider"] == "binance"
    assert out["binding_source"] == "launch57_phase1_batch1"
    assert "routes" in out
    assert out.get("failure_state") is None


@pytest.mark.asyncio
async def test_unified_exchange_connector_unavailable_when_no_routes(monkeypatch):
    async def fake_probe(symbol: str = "BTC"):
        return {"symbol": symbol, "checks": {}, "resolved": False}

    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)
    out = await unified_exchange_connector(symbol="BTC", params={})
    assert out["success"] is False
    assert out["error"] == "no_exchange_route_available"


@pytest.mark.asyncio
async def test_real_time_prices_rejects_stale_not_as_live(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 120.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["capability_id"] == 561
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "STALE"
    assert out["price"] == 100.0
    assert out.get("b1_to_41_reconciliation", {}).get("status") == "BOUND_TO_LAUNCH57_41"
    assert not any(p.get("launch_number") == 41 for p in out.get("temporal_dependency_pending", []))


@pytest.mark.asyncio
async def test_real_time_prices_live_path(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 50000.0, "source": "binance:api.binance.com", "age_sec": 1.0, "change_24h": 1.2}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["success"] is True
    assert out["presented_as_live"] is True
    assert out["freshness_state"] in {"LIVE", "NEAR_LIVE"}
    assert out["price"] == 50000.0
    assert out["unit"] == "USDT"
    assert out["legacy_runtime_dependencies"] == 0
    assert out.get("b1_to_41_reconciliation", {}).get("status") == "BOUND_TO_LAUNCH57_41"


def test_ohlcv_invariants_detect_violation():
    bad = [{"open": 10, "high": 9, "low": 8, "close": 9, "volume": 1}]
    assert validate_ohlcv_invariants(bad) != []


def test_ohlcv_invariants_pass_valid_bar():
    good = [{"open": 10, "high": 12, "low": 9, "close": 11, "volume": 100}]
    assert validate_ohlcv_invariants(good) == []


@pytest.mark.asyncio
async def test_ohlcv_full_bars_and_invariants(monkeypatch):
    bars = [
        {"open_time_ms": 1, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "volume": 5.0, "close_time_ms": 2},
    ]

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_klines(pair, interval="1h", limit=100):
        return bars, "data-api.binance.vision"

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_klines_bars", fake_klines)

    out = await ohlcv(symbol="BTC", params={"interval": "1h", "limit": 1})
    assert out["capability_id"] == 507
    assert out["success"] is True
    assert out["bars"][0]["high"] >= out["bars"][0]["open"]
    assert out["bar_count"] == 1


@pytest.mark.asyncio
async def test_quote_and_metadata_distinct_contracts(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_ticker(pair: str):
        return {"price": 42000.0, "source": "binance:api.binance.com", "change_24h": 2.0, "volume": 1000}

    async def fake_meta(pair: str):
        return {
            "canonical_symbol": "BTC",
            "display_symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "market_type": "spot",
            "status": "TRADING",
            "provider": "binance:data-api.binance.vision",
            "delisted": False,
            "precision": {"price": 2, "base": 8, "quote": 8},
        }

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)
    monkeypatch.setattr("launch57.data_batch1.fetch_symbol_exchange_metadata", fake_meta)

    from launch57.data_batch1 import quote_data

    q = await quote_data(symbol="BTC", params={})
    m = await symbol_metadata(symbol="BTC", params={})
    assert q["surface"] == "quote_data"
    assert m["surface"] == "asset_symbol_metadata"
    assert q["quote"]["last"] == 42000.0
    assert m["metadata"]["base_asset"] == "BTC"


@pytest.mark.asyncio
async def test_spot_metrics_unknown_not_zero(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": False}

    async def fake_overview(limit=20):
        return {"assets": [], "data_source": "unavailable"}

    async def fake_probe(symbol: str = "BTC"):
        return {"resolved": False}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_market_overview_pack", fake_overview)
    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)

    out = await spot_market_metrics_suite(symbol="BTC", params={})
    assert out["capability_id"] == 47
    assert out["metrics"]["price"] is None
    assert out["unknown_is_not_zero"] is True
    assert out["success"] is False


@pytest.mark.asyncio
async def test_institutional_runtime_path_uses_launch57(monkeypatch):
    async def fake_probe(symbol: str = "BTC"):
        return {
            "symbol": symbol,
            "checks": {"api.binance.com": {"ok": True, "source": "binance:api.binance.com"}},
            "resolved": True,
            "resolved_source": "binance:api.binance.com",
        }

    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)

    from cap646.institutional_official_production import execute

    out = await execute(504, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.data_batch1"
    assert out["capability_id"] == 504


@pytest.mark.asyncio
async def test_execute_dispatch_covers_batch1_caps():
    assert LAUNCH57_BATCH1_CAP_IDS == frozenset({47, 504, 506, 507, 513, 561})


@pytest.mark.asyncio
async def test_removing_launch57_binding_breaks_institutional_path(monkeypatch):
    """Regression guard — institutional path must not fall back to generic delegate."""

    async def boom(*, symbol: str, params=None):
        raise RuntimeError("launch57_spine_required")

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", boom)

    from cap646.institutional_official_production import execute

    with pytest.raises(RuntimeError, match="launch57_spine_required"):
        await execute(504, params={"symbol": "BTC"})
