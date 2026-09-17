"""B8 temporal batch — Launch #33 alert timing (SPEC §17)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.alert_timing_common import (
    B8_LAUNCH_NUMBERS,
    build_alert_timing_context,
    enrich_alert_evaluations,
)
from launch57.b8_alerts_bridge import finalize_b8_alert_surface
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _valid_alert(**extra):
    now = utc_now()
    trigger = to_rfc3339(now - timedelta(seconds=5))
    delivery_end = to_rfc3339(now + timedelta(seconds=300))
    base = {
        "trigger_time": trigger,
        "delivery_window_end": delivery_end,
        "trigger_age_ms": 5000,
    }
    base.update(extra)
    return base


def test_b8_launch_number_registry():
    assert B8_LAUNCH_NUMBERS == frozenset({33})


def test_alert_timing_preserves_spec_fields():
    alert = _valid_alert()
    timing = build_alert_timing_context({}, alert=alert)
    assert timing.trigger_time == alert["trigger_time"]
    assert timing.delivery_window["start"] == alert["trigger_time"]
    assert timing.delivery_window["end"] == alert["delivery_window_end"]
    assert timing.stale_threshold_ms == 60_000.0
    assert timing.presented_as_current is True


def test_stale_alert_not_presented_as_current():
    timing = build_alert_timing_context({}, alert=_valid_alert(trigger_age_ms=120_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "alert_stale"


def test_delivery_window_expired_not_presented_as_current():
    timing = build_alert_timing_context(
        {},
        alert=_valid_alert(
            trigger_time=_ts(-900),
            delivery_window_end=_ts(-60),
            trigger_age_ms=1000,
        ),
    )
    assert timing.presented_as_current is False
    assert timing.expired_reason == "delivery_window_expired"


def test_display_timezone_does_not_mutate_canonical_trigger_time():
    alert = _valid_alert()
    utc = build_alert_timing_context({}, alert=alert, display_timezone="UTC")
    cairo = build_alert_timing_context({}, alert=alert, display_timezone="Africa/Cairo")
    assert utc.trigger_time == cairo.trigger_time == alert["trigger_time"]
    assert utc.delivery_window["start"] == cairo.delivery_window["start"]


def test_enrich_alert_evaluations_filters_expired_from_current_fired():
    evaluations = {
        "price": {"alert_fired": True, "trigger_age_ms": 1000},
        "whale": {"alert_fired": True, "trigger_age_ms": 120_000},
    }
    enriched, current, all_fired = enrich_alert_evaluations(
        evaluations,
        ["price", "whale"],
        payload={},
    )
    assert set(all_fired) == {"price", "whale"}
    assert current == ["price"]
    assert enriched["price"]["presented_as_current"] is True
    assert enriched["whale"]["presented_as_current"] is False


def test_finalize_b8_alert_surface_fail_closed_on_expired():
    body = {
        "launch_item_id": 33,
        "success": True,
        "smart_alerts": {
            "evaluations": {
                "price": {"alert_fired": True, "trigger_age_ms": 120_000},
            },
            "fired_channels": ["price"],
        },
        "external_delivery": {"delivery_status": "BLOCKED_EXTERNAL", "external_push_live": False},
    }
    out = finalize_b8_alert_surface(body, payload={})
    assert out["success"] is False
    assert out["presented_as_current"] is False
    assert out["smart_alerts"]["fired_channels"] == []
    assert out["b8_isolation_leakage"] == 0


def test_out_of_scope_launch_noop():
    body = {"launch_item_id": 18, "success": True}
    out = finalize_b8_alert_surface(body, payload={})
    assert "alert_timing" not in out


@pytest.mark.asyncio
async def test_smart_alerts_surface_includes_b8_timing(monkeypatch):
    from failure.freshness import FreshnessState
    from launch57.derivatives_batch2 import smart_alerts_composite

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 50000.0,
            "change_24h": 5.0,
            "data_spine": {"timestamp": _ts(0), "source": "binance"},
        }

    async def fake_whale(limit=10):
        return [{"symbol": "BTC", "amount_usd": 2e6}]

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr("cap646.dedicated_common.exchange_netflow_probe", lambda p, s: ("binance", {"netflow_usd": 2e6}))
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_whale)
    monkeypatch.setattr("instant_alert_engine.engine_stats", lambda: {"enabled": True})
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.evaluate_flexible_alert_75",
        lambda user_tier, trigger: {"ok": True, "alert_fired": True, "trigger_age_ms": 1000},
    )
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **kw: {"alert_fired": True, "trigger_age_ms": 1000},
    )
    out = await smart_alerts_composite(symbol="BTC", params={})
    assert out["launch_item_id"] == 33
    assert out["b8_alert_timing"]["activated"] is True
    assert out["alert_timing"]["presented_as_current"] is True
    assert out["delivery_status"] == "BLOCKED_EXTERNAL"
    assert out["external_push_live"] is False
    assert out["b8_temporal_owner"] == "launch57.alert_timing_common"


def test_alert_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "alert_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
