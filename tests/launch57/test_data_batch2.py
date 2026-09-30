"""Launch-57 Phase 1 Data Batch 2 — isolated B2 tests."""

from __future__ import annotations

import pytest

from launch57.data_batch2 import (
    LAUNCH57_BATCH2_CAP_IDS,
    data_quality_normalization,
    data_quality_provenance_layer,
    freshness_update_assurance,
    point_in_time_immutable_metrics,
)
from launch57.point_in_time_common import reset_store_for_tests
from launch57.temporal_common import to_rfc3339, utc_now


@pytest.mark.asyncio
async def test_provenance_layer_user_disclosure():
    out = await data_quality_provenance_layer(
        symbol="BTC",
        params={
            "source_authority": "launch57:test",
            "source_time": to_rfc3339(utc_now()),
            "quality_state": "decision_grade",
        },
    )
    assert out["capability_id"] == 63
    assert out["launch_item_id"] == 40
    assert out["user_disclosure"]["question"] == "من أين الرقم؟"
    assert out["binding_source"] == "launch57_phase1_batch2"
    assert out["success"] is True
    assert out["legacy_runtime_dependencies"] == 0


@pytest.mark.asyncio
async def test_normalization_distinct_from_provenance_layer():
    out = await data_quality_normalization(
        symbol="BTC",
        params={"source_authority": "launch57:test", "quality_state": "caution", "quality_score": 60.0},
    )
    assert out["capability_id"] == 500
    assert out["launch_item_id"] == 40
    assert out["surface"] == "data_quality_normalization"
    assert out["user_disclosure"]["band"] == "caution"


@pytest.mark.asyncio
async def test_freshness_rejects_stale_as_live():
    out = await freshness_update_assurance(symbol="BTC", params={"quote_age_ms": 120_000.0, "quote_fresh": True})
    assert out["capability_id"] == 630
    assert out["launch_item_id"] == 41
    assert out["freshness_state"] == "STALE"
    assert out["presented_as_live"] is False
    assert out["success"] is False
    assert "STALE" in (out.get("delayed_label") or "")


@pytest.mark.asyncio
async def test_freshness_delayed_label_explicit():
    out = await freshness_update_assurance(symbol="BTC", params={"quote_age_ms": 30_000.0, "quote_fresh": True})
    assert out["freshness_state"] == "DELAYED"
    assert out["presented_as_live"] is True
    assert "DELAYED" in (out.get("delayed_label") or "")


@pytest.mark.asyncio
async def test_pit_immutable_metrics_hash_and_timestamp():
    reset_store_for_tests()
    out = await point_in_time_immutable_metrics(
        symbol="BTC",
        params={"metrics": {"price": 42000.0}, "source_authority": "launch57:test"},
    )
    assert out["capability_id"] == 61
    assert out["launch_item_id"] == 39
    assert out["point_in_time"] is True
    assert out["content_hash"]
    assert out["snapshot_at"]
    assert out["immutable"] is True


@pytest.mark.asyncio
async def test_institutional_runtime_path_batch2():
    from cap646.institutional_official_production import execute

    out = await execute(
        63,
        params={
            "symbol": "BTC",
            "source_authority": "launch57:test",
            "quality_state": "decision_grade",
        },
    )
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
