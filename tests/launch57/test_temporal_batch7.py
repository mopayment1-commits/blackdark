"""B7 temporal batch — cross-signal timing for regime/smart-money/derivatives (SPEC §16)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.market_regime_timing_common import (
    B7_LAUNCH_NUMBERS,
    align_signals_for_comparison,
    assess_cross_signal_timing,
    collect_signals_from_context,
    normalize_signal_input,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _signal(signal_id: str, offset_sec: float = 0, *, horizon_sec: float = 86_400, source: str = "binance"):
    return {
        "signal_id": signal_id,
        "observed_time": _ts(offset_sec),
        "horizon_sec": horizon_sec,
        "source": source,
    }


def test_b7_launch_number_registry():
    assert 7 in B7_LAUNCH_NUMBERS
    assert 37 in B7_LAUNCH_NUMBERS
    assert 30 in B7_LAUNCH_NUMBERS
    assert 8 not in B7_LAUNCH_NUMBERS
    assert 33 not in B7_LAUNCH_NUMBERS


def test_compatible_horizons_and_aligned_timestamps_pass():
    signals = [
        normalize_signal_input(_signal("a", 0, horizon_sec=3600), default_id="a"),
        normalize_signal_input(_signal("b", 10, horizon_sec=7200), default_id="b"),
    ]
    assert all(signals)
    assessment = assess_cross_signal_timing({}, [s for s in signals if s])
    assert assessment.compatible_horizons is True
    assert assessment.timestamps_aligned is True
    assert assessment.temporal_mismatch is False
    assert assessment.recommended_action == "ACT"


def test_incompatible_horizons_trigger_abstain():
    signals = [
        normalize_signal_input(_signal("short", 0, horizon_sec=60), default_id="short"),
        normalize_signal_input(_signal("long", 0, horizon_sec=86_400), default_id="long"),
    ]
    assessment = assess_cross_signal_timing({}, [s for s in signals if s])
    assert assessment.compatible_horizons is False
    assert assessment.temporal_mismatch is True
    assert assessment.recommended_action == "ABSTAIN"


def test_timestamp_skew_triggers_wait():
    signals = [
        normalize_signal_input(_signal("early", 0), default_id="early"),
        normalize_signal_input(_signal("late", 600), default_id="late"),
    ]
    assessment = assess_cross_signal_timing({}, [s for s in signals if s])
    assert assessment.timestamps_aligned is False
    assert assessment.temporal_mismatch is True
    assert assessment.recommended_action == "WAIT"


def test_live_sim_mix_triggers_abstain():
    signals = [
        normalize_signal_input(_signal("live", 0, source="binance"), default_id="live"),
        normalize_signal_input(_signal("sim", 0, source="synthetic"), default_id="sim"),
    ]
    assessment = assess_cross_signal_timing({}, [s for s in signals if s])
    assert assessment.temporal_mismatch is True
    assert assessment.recommended_action == "ABSTAIN"
    assert assessment.sim_signal_count >= 1
    assert assessment.live_signal_count >= 1


def test_align_signals_canonical_order():
    signals = [
        normalize_signal_input(_signal("b", 20), default_id="b"),
        normalize_signal_input(_signal("a", 0), default_id="a"),
    ]
    ordered = align_signals_for_comparison([s for s in signals if s])
    assert [s.signal_id for s in ordered] == ["a", "b"]


@pytest.mark.asyncio
async def test_market_regime_compass_includes_b7_timing(monkeypatch):
    from failure.freshness import FreshnessState
    from launch57.decision_batch1 import market_regime_compass

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "change_24h": 1.5,
            "data_spine": {"timestamp": _ts(0), "source": "binance"},
        }

    async def fake_onchain():
        return {}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_onchain)
    out = await market_regime_compass(symbol="BTC", params={})
    assert out["launch_item_id"] == 7
    assert out["b7_market_regime_timing"]["activated"] is True
    assert out["cross_signal_timing"]["temporal_mismatch"] is False
    assert out["b7_isolation_leakage"] == 0


@pytest.mark.asyncio
async def test_cross_market_engine_fails_closed_on_temporal_mismatch(monkeypatch):
    from failure.freshness import FreshnessState
    from launch57.decision_batch2 import cross_market_decision_engine

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 1.0,
            "data_spine": {"timestamp": _ts(0), "source": "binance"},
        }

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda **kwargs: {"ok": True, "composite_score": 80},
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda **kwargs: {"ok": True},
    )
    out = await cross_market_decision_engine(
        symbol="BTC",
        params={
            "signals": [
                _signal("live", 0, source="binance"),
                _signal("sim", 0, source="synthetic"),
            ]
        },
    )
    assert out["launch_item_id"] == 37
    assert out["success"] is False
    assert out["error"] == "temporal_mismatch"
    assert out["recommended_action"] == "ABSTAIN"


@pytest.mark.asyncio
async def test_derivatives_surface_includes_b7_timing(monkeypatch):
    from launch57.derivatives_batch1 import futures_open_interest_intelligence

    async def fake_spine(symbol, params=None):
        from failure.freshness import FreshnessState

        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "data_spine": {"timestamp": _ts(0), "source": "binance"},
        }

    async def fake_overview(symbol):
        return {"free_tier": {"open_interest_usd": 1.0}}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    out = await futures_open_interest_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 25
    assert out["cross_signal_timing"]["compatible_horizons"] is True
    assert out["b7_temporal_owner"] == "launch57.market_regime_timing_common"


def test_market_regime_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "market_regime_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
