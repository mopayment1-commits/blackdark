"""B1 → #41 targeted reconciliation tests (B1 #22/#21 only)."""

from __future__ import annotations

import pytest

from launch57.b1_freshness_bridge import apply_b1_freshness_reconciliation
from launch57.temporal_common import to_rfc3339, utc_now


def test_reconciliation_binds_freshness_and_removes_pending_41():
    body = {
        "capability_id": 561,
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
    assert out["b1_to_41_reconciliation"]["status"] == "BOUND_TO_LAUNCH57_41"
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


@pytest.mark.asyncio
async def test_real_time_prices_uses_canonical_41(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance", "temporal_dependency_pending": [], "legacy_runtime_dependencies": 0}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 1.0, "timestamp": to_rfc3339(utc_now())}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["freshness_owner"] == "launch57.freshness_common"
    assert out.get("b1_to_41_reconciliation", {}).get("status") == "BOUND_TO_LAUNCH57_41"
    assert not any(p.get("launch_number") == 41 for p in out.get("temporal_dependency_pending", []))
