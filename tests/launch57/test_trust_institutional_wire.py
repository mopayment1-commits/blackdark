"""Launch-57 Phase 2 — institutional intercept wiring for trust caps."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute


@pytest.mark.asyncio
async def test_institutional_intercepts_cap640_to_launch57(monkeypatch):
    fake_ledger = {
        "cumulative": {"metrics_scope": "live_only"},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake_ledger)
    out = await execute(640, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.trust_batch1"
    assert out["live_only_primary"] is True


@pytest.mark.asyncio
async def test_institutional_intercepts_cap639_blocks_demo(monkeypatch):
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    out = await execute(639, params={"symbol": "BTC", "opportunity": dict(FIN_004_DEMO_OPPORTUNITY)})
    assert out["handler_module"] == "launch57.trust_batch1"
    assert out["success"] is False
    assert out["error"] == "demo_opportunity_rejected"
