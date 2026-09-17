"""B11 temporal batch — personal history timing for #49–#50 (SPEC §20)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.b11_personal_history_bridge import finalize_b11_personal_history_surface
from launch57.personal_history_timing_common import (
    B11_LAUNCH_NUMBERS,
    build_personal_history_timing_context,
    enrich_history_rows,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _valid_history(**extra):
    now = utc_now()
    base = {
        "record_time": to_rfc3339(now - timedelta(seconds=60)),
        "history_validity_window_end": to_rfc3339(now + timedelta(seconds=3600)),
        "record_age_ms": 30_000,
    }
    base.update(extra)
    return base


def test_b11_launch_number_registry():
    assert B11_LAUNCH_NUMBERS == frozenset({49, 50})


def test_personal_history_timing_preserves_spec_fields():
    row = _valid_history()
    timing = build_personal_history_timing_context({}, history=row)
    assert timing.record_time == row["record_time"]
    assert timing.history_validity_window["start"] == row["record_time"]
    assert timing.history_validity_window["end"] == row["history_validity_window_end"]
    assert timing.stale_threshold_ms == 900_000.0
    assert timing.presented_as_current is True


def test_stale_history_not_presented_as_current():
    timing = build_personal_history_timing_context({}, history=_valid_history(record_age_ms=1_000_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "history_record_stale"


def test_history_validity_expired_not_presented_as_current():
    timing = build_personal_history_timing_context(
        {},
        history=_valid_history(
            record_time=_ts(-900000),
            history_validity_window_end=_ts(-60),
            record_age_ms=1000,
        ),
    )
    assert timing.presented_as_current is False
    assert timing.expired_reason == "history_validity_expired"


def test_display_timezone_does_not_mutate_canonical_record_time():
    row = _valid_history()
    utc = build_personal_history_timing_context({}, history=row, display_timezone="UTC")
    cairo = build_personal_history_timing_context({}, history=row, display_timezone="Africa/Cairo")
    assert utc.record_time == cairo.record_time == row["record_time"]
    assert utc.history_validity_window["start"] == cairo.history_validity_window["start"]


def test_enrich_history_rows_filters_expired_from_current():
    rows = [
        _valid_history(id="fresh", record_age_ms=1000),
        _valid_history(id="stale", record_age_ms=1_000_000),
    ]
    current, all_rows = enrich_history_rows(rows, payload={})
    assert len(all_rows) == 2
    assert len(current) == 1
    assert current[0]["id"] == "fresh"
    assert all_rows[1]["presented_as_current"] is False


def test_finalize_b11_personal_history_surface_fail_closed_on_expired():
    body = {
        "launch_item_id": 49,
        "success": True,
        "personal_decision_history": {
            "decisions": [_valid_history(id="stale", record_age_ms=1_000_000)],
            "count": 1,
        },
    }
    out = finalize_b11_personal_history_surface(body, payload={})
    assert out["success"] is False
    assert out["presented_as_current"] is False
    assert out["personal_decision_history"]["decisions"] == []
    assert out["b11_isolation_leakage"] == 0


def test_out_of_scope_launch_noop():
    body = {"launch_item_id": 52, "success": True}
    out = finalize_b11_personal_history_surface(body, payload={})
    assert "personal_history_timing" not in out


@pytest.mark.asyncio
async def test_personal_decision_history_includes_b11_timing(monkeypatch):
    from launch57.edge_ui_batch1 import personal_decision_history

    monkeypatch.setattr(
        "launch57.edge_ui_common.read_decision_history_rows",
        lambda limit, tier: [{"decision_id": "d1", "record_age_ms": 1000, "record_time": _ts(0)}],
    )
    out = await personal_decision_history(symbol="BTC", params={"tier": "free"})
    assert out["launch_item_id"] == 49
    assert out["b11_personal_history_timing"]["activated"] is True
    assert out["personal_history_timing"]["presented_as_current"] is True
    assert out["b11_temporal_owner"] == "launch57.personal_history_timing_common"


@pytest.mark.asyncio
async def test_discipline_mirror_includes_b11_timing(monkeypatch):
    from launch57.edge_ui_batch1 import discipline_mirror_light

    monkeypatch.setattr(
        "discipline_mirror.personal_mirror",
        lambda user_key, limit: {
            "entries": [{"id": "m1", "record_age_ms": 1000, "record_time": _ts(0)}],
            "lightweight": True,
        },
    )
    out = await discipline_mirror_light(symbol="BTC", params={"user_key": "u1"})
    assert out["launch_item_id"] == 50
    assert out["personal_history_timing"]["record_time"]
    assert out["discipline_mirror"]["presented_as_current_only"] is True


def test_personal_history_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "personal_history_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
