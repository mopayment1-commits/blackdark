"""Launch-57 temporal B3 tests — #6 evidence class (LIVE/DELAYED/SIM)."""

from __future__ import annotations

import pytest

from launch57.evidence_class_common import (
    assess_user_evidence_class,
    attach_evidence_class_metadata,
    infer_canonical_evidence_class,
)


def test_infer_canonical_from_source_hints():
    assert infer_canonical_evidence_class(source="market_replay_v1") == "BACKTESTED"
    assert infer_canonical_evidence_class(source="synthetic") == "SIMULATED"
    assert infer_canonical_evidence_class(source="binance:live") == "SHADOW_LIVE_FORWARD"


def test_user_label_live_delayed_sim():
    live = assess_user_evidence_class({"evidence_class": "PRODUCTION_VERIFIED"})
    assert live.user_facing_label == "LIVE"
    assert live.visible is True

    delayed = assess_user_evidence_class({"source": "market_replay_v1"})
    assert delayed.user_facing_label == "DELAYED"

    sim = assess_user_evidence_class({"source": "synthetic"})
    assert sim.user_facing_label == "SIM"


def test_display_timezone_does_not_alter_evidence_class():
    base = assess_user_evidence_class({"evidence_class": "PRODUCTION_VERIFIED"})
    cairo = assess_user_evidence_class({"evidence_class": "PRODUCTION_VERIFIED"}, display_timezone="Africa/Cairo")
    utc = assess_user_evidence_class({"evidence_class": "PRODUCTION_VERIFIED"}, display_timezone="UTC")
    assert base.user_facing_label == cairo.user_facing_label == utc.user_facing_label == "LIVE"
    assert cairo.display_timezone_invariant is True


def test_stale_freshness_downgrades_live_to_delayed():
    out = assess_user_evidence_class(
        {"evidence_class": "PRODUCTION_VERIFIED", "freshness_state": "STALE"},
        freshness_state="STALE",
    )
    assert out.user_facing_label == "DELAYED"
    assert out.freshness_downgrade_applied is True


def test_attach_evidence_class_metadata_sets_owner():
    body = attach_evidence_class_metadata({"source": "binance", "success": True})
    assert body["evidence_class_owner"] == "launch57.evidence_class_common"
    assert body["evidence_class_visible"] is True
    assert body["evidence_display"]["launch_item_id"] == 6


@pytest.mark.asyncio
async def test_b1_path_attaches_evidence_class_when_b3_activated(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        from launch57.temporal_common import to_rfc3339, utc_now

        return {"price": 1.0, "source": "binance", "age_sec": 1.0, "timestamp": to_rfc3339(utc_now())}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["evidence_class_owner"] == "launch57.evidence_class_common"
    assert out["evidence_display"]["user_facing_label"] == "LIVE"
    assert not any(p.get("launch_number") == 6 for p in out.get("temporal_dependency_pending", []))
    assert out["b3_evidence_reconciliation"]["status"] == "PENDING_VERIFICATION"


@pytest.mark.asyncio
async def test_b2_path_attaches_evidence_class_when_b3_activated():
    from launch57.data_batch2 import freshness_update_assurance

    out = await freshness_update_assurance(symbol="BTC", params={"quote_age_ms": 1000.0})
    assert out["evidence_class_owner"] == "launch57.evidence_class_common"
    assert "evidence_display" in out
    assert not any(p.get("launch_number") == 6 for p in out.get("temporal_dependency_pending", []))
