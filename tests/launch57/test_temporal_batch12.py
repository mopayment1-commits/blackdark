"""B12 temporal batch — due diligence / risk timing for #53–#57 (SPEC §21)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.b12_due_diligence_risk_bridge import finalize_b12_due_diligence_risk_surface
from launch57.due_diligence_risk_timing_common import (
    B12_LAUNCH_NUMBERS,
    build_due_diligence_risk_timing_context,
    enrich_risk_incident_rows,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _valid_risk(**extra):
    now = utc_now()
    base = {
        "last_update_time": to_rfc3339(now - timedelta(seconds=60)),
        "risk_validity_window_end": to_rfc3339(now + timedelta(seconds=3600)),
        "source_age_ms": 30_000,
    }
    base.update(extra)
    return base


def test_b12_launch_number_registry():
    assert B12_LAUNCH_NUMBERS == frozenset({53, 54, 55, 56, 57})


def test_due_diligence_risk_timing_preserves_spec_fields():
    row = _valid_risk()
    timing = build_due_diligence_risk_timing_context({}, risk=row)
    assert timing.last_update_time == row["last_update_time"]
    assert timing.risk_validity_window["start"] == row["last_update_time"]
    assert timing.risk_validity_window["end"] == row["risk_validity_window_end"]
    assert timing.source_age_ms == 30_000
    assert timing.stale_threshold_ms == 900_000.0
    assert timing.presented_as_current is True


def test_stale_risk_not_presented_as_current():
    timing = build_due_diligence_risk_timing_context({}, risk=_valid_risk(source_age_ms=1_000_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_source_stale"


def test_risk_validity_expired_not_presented_as_current():
    timing = build_due_diligence_risk_timing_context(
        {},
        risk=_valid_risk(
            last_update_time=_ts(-900000),
            risk_validity_window_end=_ts(-60),
            source_age_ms=1000,
        ),
    )
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_validity_expired"


def test_display_timezone_does_not_mutate_canonical_last_update_time():
    row = _valid_risk()
    utc = build_due_diligence_risk_timing_context({}, risk=row, display_timezone="UTC")
    cairo = build_due_diligence_risk_timing_context({}, risk=row, display_timezone="Africa/Cairo")
    assert utc.last_update_time == cairo.last_update_time == row["last_update_time"]
    assert utc.risk_validity_window["start"] == cairo.risk_validity_window["start"]


def test_enrich_risk_incident_rows_filters_expired_from_current():
    rows = [
        _valid_risk(id="fresh", source_age_ms=1000),
        _valid_risk(id="stale", source_age_ms=1_000_000),
    ]
    current, all_rows = enrich_risk_incident_rows(rows, payload={})
    assert len(all_rows) == 2
    assert len(current) == 1
    assert current[0]["id"] == "fresh"
    assert all_rows[1]["presented_as_current"] is False


def test_enrich_risk_incident_rows_preserves_chronology():
    rows = [
        _valid_risk(id="a", last_update_time=_ts(-120)),
        _valid_risk(id="b", last_update_time=_ts(-60)),
    ]
    current, all_rows = enrich_risk_incident_rows(rows, payload={})
    assert [r["id"] for r in all_rows] == ["a", "b"]
    assert [r["id"] for r in current] == ["a", "b"]


def test_finalize_b12_due_diligence_risk_surface_fail_closed_on_expired():
    body = {
        "launch_item_id": 53,
        "success": True,
        "due_diligence": {
            "verdict": "review",
            "source_age_ms": 1_000_000,
            "last_update_time": _ts(-60),
        },
    }
    out = finalize_b12_due_diligence_risk_surface(body, payload={})
    assert out["success"] is False
    assert out["presented_as_current"] is False
    assert out["b12_isolation_leakage"] == 0


def test_out_of_scope_launch_noop():
    body = {"launch_item_id": 15, "success": True}
    out = finalize_b12_due_diligence_risk_surface(body, payload={})
    assert "due_diligence_risk_timing" not in out


def test_missing_last_update_and_source_age_not_current():
    timing = build_due_diligence_risk_timing_context({}, risk={})
    assert timing.last_update_time is None
    assert timing.source_age_ms is None
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_timestamp_unknown"


def test_string_only_risk_flags_without_timestamp_not_falsely_current():
    body = {
        "launch_item_id": 53,
        "success": True,
        "due_diligence": {"risk_flags": ["elevated_surveillance_pattern"], "verdict": "review"},
    }
    out = finalize_b12_due_diligence_risk_surface(body, payload={})
    assert out["presented_as_current"] is False
    assert out["due_diligence_risk_timing"]["last_update_time"] is None
    assert out["due_diligence_risk_timing"]["expired_reason"] == "risk_timestamp_unknown"


def test_timestamp_missing_incident_row_not_falsely_current():
    timing = build_due_diligence_risk_timing_context({}, risk={"id": "old_incident", "severity": "high"})
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_timestamp_unknown"
    current, all_rows = enrich_risk_incident_rows(
        [{"id": "old_incident", "severity": "high"}],
        payload={},
    )
    assert current == []
    assert all_rows[0]["presented_as_current"] is False


def test_explicit_valid_timestamp_remains_current():
    timing = build_due_diligence_risk_timing_context({}, risk=_valid_risk())
    assert timing.presented_as_current is True
    assert timing.last_update_time is not None


def test_explicit_stale_source_age_remains_stale():
    timing = build_due_diligence_risk_timing_context({}, risk=_valid_risk(source_age_ms=1_000_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_source_stale"


def test_stale_source_age_without_last_update_remains_stale():
    timing = build_due_diligence_risk_timing_context({}, risk={"source_age_ms": 1_000_000})
    assert timing.presented_as_current is False
    assert timing.expired_reason == "risk_source_stale"
    assert timing.last_update_time is None


async def _fake_spine(symbol, params):
    return {
        "symbol": symbol,
        "live_eligible": True,
        "freshness_state": "FRESH",
        "data_spine": {"timestamp": _ts(0)},
        "presented_as_live": True,
    }


async def _fake_search_address(address, *, chain="ethereum"):
    return {"ok": True, "entity_label": "test"}


@pytest.mark.asyncio
async def test_instant_wallet_due_diligence_includes_b12_timing(monkeypatch):
    import bd_platform.address_intelligence as address_intel
    from launch57.smart_money_batch2 import instant_wallet_due_diligence

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", _fake_spine)
    monkeypatch.setattr(address_intel, "search_address", _fake_search_address)
    monkeypatch.setattr(
        "bd_platform.whales_institutional_layer.analyze_wallet_surveillance_79",
        lambda wallet: {"surveillance_detected": False},
    )
    out = await instant_wallet_due_diligence(
        symbol="BTC",
        params={"address": "0xabc", "governed_payload": {"source_age_ms": 1000, "last_update_time": _ts(0)}},
    )
    assert out["launch_item_id"] == 53
    assert out["b12_due_diligence_risk_timing"]["activated"] is True
    assert out["due_diligence_risk_timing"]["presented_as_current"] is True
    assert out["b12_temporal_owner"] == "launch57.due_diligence_risk_timing_common"


@pytest.mark.asyncio
async def test_suspicious_activity_flags_includes_b12_timing(monkeypatch):
    import bd_platform.derivatives_onchain_intelligence_layer as fraud_layer
    from launch57.smart_money_batch3 import suspicious_activity_flags

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", _fake_spine)
    monkeypatch.setattr(
        fraud_layer,
        "fraud_suspicious_activity_297",
        lambda seed: {
            "flags": [
                {"id": "f1", "source_age_ms": 1000, "last_update_time": _ts(0)},
            ]
        },
    )
    out = await suspicious_activity_flags(symbol="BTC", params={})
    assert out["launch_item_id"] == 56
    assert out["due_diligence_risk_timing"]["last_update_time"]
    assert out["presented_as_current_only"] is True


def test_due_diligence_risk_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "due_diligence_risk_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
