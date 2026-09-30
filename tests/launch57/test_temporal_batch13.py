"""B13 temporal batch — chart display timezone consistency (SPEC §22, cross-cutting)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from launch57.b13_chart_display_bridge import finalize_b13_chart_surface
from launch57.chart_display_timing_common import (
    CHART_COMPONENT_NAMES,
    build_chart_display_timing_context,
    bind_chart_components,
    is_chart_bearing_body,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _bar(open_time_ms: int) -> dict:
    return {
        "open_time_ms": open_time_ms,
        "open": 1.0,
        "high": 2.0,
        "low": 0.5,
        "close": 1.5,
        "volume": 10.0,
    }


def test_b13_chart_component_registry():
    assert CHART_COMPONENT_NAMES == ("candles", "axes", "crosshair", "annotations", "events", "tooltips")


def test_is_chart_bearing_body_ohlcv_surface():
    assert is_chart_bearing_body({"surface": "ohlcv"}) is True
    assert is_chart_bearing_body({"surface": "quote_data"}) is False


def test_single_display_timezone_bound_to_all_components():
    body = bind_chart_components(
        {"surface": "ohlcv", "bars": [_bar(1_700_000_000_000)]},
        display_timezone="Africa/Cairo",
    )
    view = body["chart_view"]
    assert view["display_timezone"] == "Africa/Cairo"
    assert view["axes"]["x"]["display_timezone"] == "Africa/Cairo"
    assert view["crosshair"]["display_timezone"] == "Africa/Cairo"
    assert view["tooltips"]["display_timezone"] == "Africa/Cairo"
    assert body["candles"][0]["canonical_open_time"]
    assert body["candles"][0]["local_render_open_time"]


def test_display_timezone_does_not_mutate_canonical_open_time():
    bar = _bar(1_700_000_000_000)
    utc_body = bind_chart_components({"bars": [bar]}, display_timezone="UTC")
    cairo_body = bind_chart_components({"bars": [bar]}, display_timezone="Africa/Cairo")
    assert utc_body["candles"][0]["canonical_open_time"] == cairo_body["candles"][0]["canonical_open_time"]
    assert utc_body["candles"][0]["open_time_ms"] == bar["open_time_ms"]


def test_timezone_mixing_fail_closed():
    body = {
        "surface": "ohlcv",
        "bars": [_bar(1_700_000_000_000)],
        "chart_view": {
            "display_timezone": "UTC",
            "axes": {"x": {"display_timezone": "America/New_York"}},
        },
    }
    out = finalize_b13_chart_surface(body, payload={})
    assert out["chart_temporally_consistent"] is False
    assert out["success"] is False
    assert out["chart_display_timing"]["expired_reason"] == "chart_timezone_mixing"
    assert out["b13_isolation_leakage"] == 0


def test_non_chart_surface_noop():
    body = {"surface": "quote_data", "success": True}
    out = finalize_b13_chart_surface(body, payload={})
    assert "chart_display_timing" not in out


def test_build_chart_display_timing_context_consistent_view():
    timing = build_chart_display_timing_context(
        {},
        chart_view={
            "display_timezone": "UTC",
            "axes": {"x": {"display_timezone": "UTC"}},
            "crosshair": {"display_timezone": "UTC"},
            "tooltips": {"display_timezone": "UTC"},
        },
        display_timezone="UTC",
    )
    assert timing.chart_temporally_consistent is True
    assert timing.timezone_mixing_detected is False


@pytest.mark.asyncio
async def test_ohlcv_includes_b13_chart_timing(monkeypatch):
    from launch57.data_batch1 import ohlcv

    bars = [_bar(1_700_000_000_000)]

    async def fake_connector(symbol, params):
        return {"success": True}

    async def fake_klines(pair, interval, limit):
        return bars, "data-api.binance.vision"

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_klines_bars", fake_klines)

    out = await ohlcv(symbol="BTC", params={"interval": "1h", "display_timezone": "UTC"})
    assert out["surface"] == "ohlcv"
    assert out["b13_chart_display_timing"]["activated"] is True
    assert out["chart_display_timing"]["chart_temporally_consistent"] is True
    assert out["chart_view"]["candles"][0]["canonical_open_time"]
    assert out["b13_temporal_owner"] == "launch57.chart_display_timing_common"


def test_chart_display_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "chart_display_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
