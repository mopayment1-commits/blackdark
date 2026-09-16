"""Launch-57 Phase 1 Data Batch 2 — quality, freshness, PIT metrics tests."""

from __future__ import annotations

import pytest

from launch57.data_batch2 import (
    LAUNCH57_BATCH2_CAP_IDS,
    data_quality_normalization,
    data_quality_provenance_layer,
    freshness_update_assurance,
    point_in_time_immutable_metrics,
)


@pytest.mark.asyncio
async def test_provenance_layer_user_disclosure(monkeypatch):
    def fake_prov(symbol: str):
        return {
            "provenance": {"band": "decision_grade", "score": 85.0, "posture": "ok", "honesty": "live only"},
            "hot_storage": {"rows": 1},
        }

    monkeypatch.setattr("cap646.dedicated_common.provenance_hot_storage_payload", fake_prov)
    out = await data_quality_provenance_layer(symbol="BTC", params={})
    assert out["capability_id"] == 63
    assert out["launch_item_id"] == 40
    assert out["user_disclosure"]["question"] == "من أين الرقم؟"
    assert out["binding_source"] == "launch57_phase1_batch2"
    assert out["success"] is True


@pytest.mark.asyncio
async def test_normalization_distinct_from_provenance_layer(monkeypatch):
    async def fake_norm(*, symbol: str = "BTC"):
        return {
            "capability_id": 500,
            "schema_version": "canonical_v1",
            "provenance": {"band": "caution", "score": 60.0},
            "success": True,
        }

    monkeypatch.setattr("cap646.data_spine.normalization_report", fake_norm)
    out = await data_quality_normalization(symbol="BTC", params={})
    assert out["capability_id"] == 500
    assert out["launch_item_id"] == 40
    assert out["surface"] == "data_quality_normalization"
    assert out["user_disclosure"]["provenance_band"] == "caution"


@pytest.mark.asyncio
async def test_freshness_rejects_stale_as_live(monkeypatch):
    async def fake_fresh(*, symbol: str = "BTC"):
        return {
            "capability_id": 630,
            "quote_fresh": True,
            "quote_age_ms": 120_000.0,
            "success": True,
        }

    monkeypatch.setattr("cap646.data_spine.freshness_assurance_report", fake_fresh)
    out = await freshness_update_assurance(symbol="BTC", params={})
    assert out["capability_id"] == 630
    assert out["launch_item_id"] == 41
    assert out["freshness_state"] == "STALE"
    assert out["presented_as_live"] is False
    assert out["success"] is False
    assert "STALE" in (out.get("delayed_label") or "")


@pytest.mark.asyncio
async def test_freshness_delayed_label_explicit(monkeypatch):
    async def fake_fresh(*, symbol: str = "BTC"):
        return {"quote_fresh": True, "quote_age_ms": 30_000.0, "success": True}

    monkeypatch.setattr("cap646.data_spine.freshness_assurance_report", fake_fresh)
    out = await freshness_update_assurance(symbol="BTC", params={})
    assert out["freshness_state"] == "DELAYED"
    assert out["presented_as_live"] is True
    assert "DELAYED" in (out.get("delayed_label") or "")


@pytest.mark.asyncio
async def test_pit_immutable_metrics_hash_and_timestamp(monkeypatch):
    def fake_track():
        return {"immutable_chain": {"valid": True, "total_records": 5}, "cumulative": {"metrics_scope": "live_only"}}

    class Hot:
        rows = 2

    monkeypatch.setattr("oracle_track_record.public_track_record", fake_track)
    monkeypatch.setattr("hot_storage.get_hot_storage_stats", lambda: Hot())
    out = await point_in_time_immutable_metrics(symbol="BTC", params={})
    assert out["capability_id"] == 61
    assert out["launch_item_id"] == 39
    assert out["point_in_time"] is True
    assert out["content_hash"]
    assert out["snapshot_at"]
    assert out["immutable"] is True


@pytest.mark.asyncio
async def test_institutional_runtime_path_batch2(monkeypatch):
    def fake_prov(symbol: str):
        return {"provenance": {"band": "decision_grade", "score": 80}, "hot_storage": {}}

    monkeypatch.setattr("cap646.dedicated_common.provenance_hot_storage_payload", fake_prov)
    from cap646.institutional_official_production import execute

    out = await execute(63, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.data_batch2"
    assert out["capability_id"] == 63


@pytest.mark.asyncio
async def test_removing_launch57_batch2_binding_raises(monkeypatch):
    async def boom(*, symbol: str, params=None):
        raise RuntimeError("launch57_batch2_required")

    monkeypatch.setattr("launch57.data_batch2.data_quality_provenance_layer", boom)

    from cap646.institutional_official_production import execute

    with pytest.raises(RuntimeError, match="launch57_batch2_required"):
        await execute(63, params={"symbol": "BTC"})


def test_batch2_cap_ids():
    assert LAUNCH57_BATCH2_CAP_IDS == frozenset({61, 63, 500, 630})
