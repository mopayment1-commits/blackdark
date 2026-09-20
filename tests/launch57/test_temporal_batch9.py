"""B9 temporal batch — research/explanation timing for #34–#36, #51 (SPEC §18)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.b9_research_explanation_bridge import finalize_b9_explanation_surface
from launch57.research_explanation_timing_common import (
    B9_LAUNCH_NUMBERS,
    build_explanation_timing_context,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _valid_explanation(**extra):
    now = utc_now()
    base = {
        "generation_time": to_rfc3339(now - timedelta(seconds=10)),
        "validity_window_end": to_rfc3339(now + timedelta(seconds=1800)),
        "source_age_ms": 10_000,
    }
    base.update(extra)
    return base


def test_b9_launch_number_registry():
    assert B9_LAUNCH_NUMBERS == frozenset({34, 35, 36, 51})


def test_explanation_timing_preserves_spec_fields():
    row = _valid_explanation()
    timing = build_explanation_timing_context({}, explanation=row)
    assert timing.generation_time == row["generation_time"]
    assert timing.validity_window["start"] == row["generation_time"]
    assert timing.validity_window["end"] == row["validity_window_end"]
    assert timing.stale_threshold_ms == 300_000.0
    assert timing.presented_as_current is True


def test_stale_explanation_not_presented_as_current():
    timing = build_explanation_timing_context({}, explanation=_valid_explanation(source_age_ms=400_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "explanation_source_stale"


def test_validity_window_expired_not_presented_as_current():
    timing = build_explanation_timing_context(
        {},
        explanation=_valid_explanation(
            generation_time=_ts(-7200),
            validity_window_end=_ts(-60),
            source_age_ms=1000,
        ),
    )
    assert timing.presented_as_current is False
    assert timing.expired_reason == "validity_window_expired"


def test_display_timezone_does_not_mutate_canonical_generation_time():
    row = _valid_explanation()
    utc = build_explanation_timing_context({}, explanation=row, display_timezone="UTC")
    cairo = build_explanation_timing_context({}, explanation=row, display_timezone="Africa/Cairo")
    assert utc.generation_time == cairo.generation_time == row["generation_time"]
    assert utc.validity_window["start"] == cairo.validity_window["start"]


def test_finalize_b9_explanation_surface_fail_closed_on_expired():
    body = {
        "launch_item_id": 34,
        "success": True,
        "explanation": {"ready": True, "source_age_ms": 400_000},
    }
    out = finalize_b9_explanation_surface(body, payload={})
    assert out["success"] is False
    assert out["presented_as_current"] is False
    assert out["error"] == "explanation_source_stale"
    assert out["b9_isolation_leakage"] == 0


def test_out_of_scope_launch_noop():
    body = {"launch_item_id": 33, "success": True}
    out = finalize_b9_explanation_surface(body, payload={})
    assert "explanation_timing" not in out


@pytest.mark.asyncio
async def test_signal_explanation_includes_b9_timing(monkeypatch):
    from failure.freshness import FreshnessState
    from launch57.explanation_ai_batch1 import signal_explanation_workflow

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "data_spine": {"timestamp": _ts(0), "source": "binance"},
        }

    async def fake_footprint(symbol):
        return {"symbol": symbol, "ok": True}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", fake_footprint)
    monkeypatch.setattr(
        "heroes_quality.build_oqs_why_block",
        lambda ctx: {"ready": True, "summary": "test"},
    )
    out = await signal_explanation_workflow(symbol="BTC", params={})
    assert out["launch_item_id"] == 34
    assert out["b9_research_explanation_timing"]["activated"] is True
    assert out["explanation_timing"]["presented_as_current"] is True
    assert out["b9_temporal_owner"] == "launch57.research_explanation_timing_common"


@pytest.mark.asyncio
async def test_research_portal_includes_b9_timing(monkeypatch):
    from launch57.explanation_ai_batch1 import research_intelligence_portal

    monkeypatch.setattr(
        "oracle_track_record.public_track_record",
        lambda: {"cumulative": {"resolved_predictions": 5, "hit_rate_percent": 60}},
    )
    out = await research_intelligence_portal(symbol="BTC", params={})
    assert out["launch_item_id"] == 51
    assert out["explanation_timing"]["generation_time"]
    assert out["explanation_timing"]["presented_as_current"] is True


def test_research_explanation_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "research_explanation_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
