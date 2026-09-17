"""B1 → #41 targeted reconciliation tests (B1 #22/#21 only)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from launch57.b1_freshness_bridge import (
    B1_TO_41_RECONCILIATION_ACTIVATED,
    apply_b1_freshness_reconciliation,
    prepare_b1_freshness_path,
)
from launch57.temporal_common import to_rfc3339, utc_now


def test_prepare_keeps_pending_41_and_blocks_freshness():
    body = {
        "capability_id": 561,
        "price_data_available": True,
        "success": True,
        "temporal": {
            "observed_time": to_rfc3339(utc_now()),
            "ingested_at": to_rfc3339(utc_now()),
            "available_at": to_rfc3339(utc_now()),
            "availability_state": "KNOWN",
        },
    }
    out = prepare_b1_freshness_path(body)
    assert out["b1_to_41_reconciliation"]["status"] == "PREPARED_NOT_ACTIVATED"
    assert out["freshness_semantics"] == "BLOCKED_BY_DEPENDENCY_ORDER"
    assert out["presented_as_live"] is False
    assert any(p.get("launch_number") == 41 for p in out["temporal_dependency_pending"])


def test_reconciliation_inert_when_gate_closed(monkeypatch):
    monkeypatch.setattr("launch57.b1_freshness_bridge.B1_TO_41_RECONCILIATION_ACTIVATED", False)
    body = {
        "price_data_available": True,
        "success": True,
        "temporal_dependency_pending": [
            {"launch_number": 41, "status": "TEMPORAL_DEPENDENCY_PENDING"},
            {"launch_number": 6, "status": "TEMPORAL_DEPENDENCY_PENDING"},
        ],
        "temporal": {
            "observed_time": to_rfc3339(utc_now()),
            "ingested_at": to_rfc3339(utc_now()),
            "available_at": to_rfc3339(utc_now()),
            "availability_state": "KNOWN",
        },
    }
    out = apply_b1_freshness_reconciliation(body, age_sec=1.0)
    assert out["b1_to_41_reconciliation"]["status"] == "PREPARED_NOT_ACTIVATED"
    assert any(p.get("launch_number") == 41 for p in out["temporal_dependency_pending"])
    assert out["presented_as_live"] is False


def test_reconciliation_activated_binds_canonical_41():
    assert B1_TO_41_RECONCILIATION_ACTIVATED is True
    body = {
        "price_data_available": True,
        "success": True,
        "temporal_dependency_pending": [
            {"launch_number": 41, "status": "TEMPORAL_DEPENDENCY_PENDING"},
            {"launch_number": 6, "status": "TEMPORAL_DEPENDENCY_PENDING"},
        ],
        "temporal": {
            "observed_time": to_rfc3339(utc_now()),
            "ingested_at": to_rfc3339(utc_now()),
            "available_at": to_rfc3339(utc_now()),
            "availability_state": "KNOWN",
        },
    }
    out = apply_b1_freshness_reconciliation(body, age_sec=1.0)
    assert out["b1_to_41_reconciliation"]["status"] == "PENDING_VERIFICATION"
    assert out["b1_to_41_reconciliation"]["binding_status"] == "ACTIVATED_BOUND_TO_LAUNCH57_41"
    assert not any(p.get("launch_number") == 41 for p in out["temporal_dependency_pending"])
    assert any(p.get("launch_number") == 6 for p in out["temporal_dependency_pending"])
    assert out["freshness_owner"] == "launch57.freshness_common"
    assert "freshness_semantics" not in out


def test_reconciliation_stale_age_not_live():
    body = {
        "price_data_available": True,
        "success": True,
        "temporal": {
            "observed_time": to_rfc3339(utc_now()),
            "ingested_at": to_rfc3339(utc_now()),
            "available_at": to_rfc3339(utc_now()),
            "availability_state": "KNOWN",
        },
    }
    out = apply_b1_freshness_reconciliation(body, age_sec=120.0)
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "STALE"


def test_reconciliation_unknown_age_not_live():
    out = apply_b1_freshness_reconciliation(
        {"success": True, "temporal": {"availability_state": "UNKNOWN"}},
        age_sec=None,
    )
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "UNKNOWN"


def test_reconciliation_delayed_label_explicit():
    out = apply_b1_freshness_reconciliation(
        {
            "success": True,
            "temporal": {
                "observed_time": to_rfc3339(utc_now()),
                "available_at": to_rfc3339(utc_now()),
                "availability_state": "KNOWN",
            },
        },
        age_sec=30.0,
    )
    assert out["freshness_state"] == "DELAYED"
    assert out["presented_as_live"] is True
    assert "DELAYED" in (out.get("delayed_label") or "")


def test_reconciliation_future_timestamp_fails_closed():
    future = to_rfc3339(utc_now() + timedelta(hours=3))
    out = apply_b1_freshness_reconciliation(
        {"success": True, "temporal": {"observed_time": to_rfc3339(utc_now())}},
        age_sec=1.0,
        source_time=future,
    )
    assert out["presented_as_live"] is False
    assert out["success"] is False


def test_reconciliation_gate_regression_removal_would_restore_pending_41(monkeypatch):
    monkeypatch.setattr("launch57.b1_freshness_bridge.B1_TO_41_RECONCILIATION_ACTIVATED", False)
    out = apply_b1_freshness_reconciliation({"success": True}, age_sec=1.0)
    assert any(p.get("launch_number") == 41 for p in out["temporal_dependency_pending"])
    assert out.get("freshness_semantics") == "BLOCKED_BY_DEPENDENCY_ORDER"


@pytest.mark.asyncio
async def test_real_time_prices_fresh_under_canonical_41(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 1.0, "timestamp": to_rfc3339(utc_now())}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["b1_to_41_reconciliation"]["status"] == "PENDING_VERIFICATION"
    assert out["presented_as_live"] is True
    assert out["freshness_owner"] == "launch57.freshness_common"
    assert not any(p.get("launch_number") == 41 for p in out.get("temporal_dependency_pending", []))


@pytest.mark.asyncio
async def test_real_time_prices_stale_not_live(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 120.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "STALE"
    assert out["price"] == 100.0


@pytest.mark.asyncio
async def test_spot_metrics_fresh_under_canonical_41(monkeypatch):
    from launch57.data_batch1 import spot_market_metrics_suite

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_overview(limit=20):
        return {"assets": [{"symbol": "BTC", "price": 1.0}], "data_source": "binance"}

    async def fake_probe(symbol: str = "BTC"):
        return {"resolved": True}

    async def fake_ticker(pair: str):
        return {"price": 1.0, "source": "binance", "age_sec": 1.0, "timestamp": to_rfc3339(utc_now())}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_market_overview_pack", fake_overview)
    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await spot_market_metrics_suite(symbol="BTC", params={})
    assert out["launch_item_id"] == 21
    assert out["presented_as_live"] is True
    assert out["freshness_owner"] == "launch57.freshness_common"


@pytest.mark.asyncio
async def test_spot_metrics_stale_not_live(monkeypatch):
    from launch57.data_batch1 import spot_market_metrics_suite

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_overview(limit=20):
        return {"assets": [], "data_source": "binance"}

    async def fake_probe(symbol: str = "BTC"):
        return {"resolved": True}

    async def fake_ticker(pair: str):
        return {"price": 1.0, "source": "binance", "age_sec": 120.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_market_overview_pack", fake_overview)
    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await spot_market_metrics_suite(symbol="BTC", params={})
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "STALE"
