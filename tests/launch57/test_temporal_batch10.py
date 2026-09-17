"""B10 temporal batch — shareable/public timing for #44–#46 (SPEC §19)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.b10_shareable_public_bridge import finalize_b10_shareable_surface
from launch57.shareable_public_timing_common import (
    B10_LAUNCH_NUMBERS,
    build_shareable_public_timing_context,
)
from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


def _valid_share(**extra):
    now = utc_now()
    base = {
        "publication_time": to_rfc3339(now - timedelta(seconds=30)),
        "public_validity_window_end": to_rfc3339(now + timedelta(seconds=3600)),
        "content_age_ms": 15_000,
    }
    base.update(extra)
    return base


def test_b10_launch_number_registry():
    assert B10_LAUNCH_NUMBERS == frozenset({44, 45, 46})


def test_shareable_public_timing_preserves_spec_fields():
    row = _valid_share()
    timing = build_shareable_public_timing_context({}, content=row)
    assert timing.publication_time == row["publication_time"]
    assert timing.public_validity_window["start"] == row["publication_time"]
    assert timing.public_validity_window["end"] == row["public_validity_window_end"]
    assert timing.stale_threshold_ms == 600_000.0
    assert timing.presented_as_current is True


def test_stale_share_not_presented_as_current():
    timing = build_shareable_public_timing_context({}, content=_valid_share(content_age_ms=700_000))
    assert timing.presented_as_current is False
    assert timing.expired_reason == "share_content_stale"


def test_public_validity_expired_not_presented_as_current():
    timing = build_shareable_public_timing_context(
        {},
        content=_valid_share(
            publication_time=_ts(-90000),
            public_validity_window_end=_ts(-60),
            content_age_ms=1000,
        ),
    )
    assert timing.presented_as_current is False
    assert timing.expired_reason == "public_validity_expired"


def test_display_timezone_does_not_mutate_canonical_publication_time():
    row = _valid_share()
    utc = build_shareable_public_timing_context({}, content=row, display_timezone="UTC")
    cairo = build_shareable_public_timing_context({}, content=row, display_timezone="Africa/Cairo")
    assert utc.publication_time == cairo.publication_time == row["publication_time"]
    assert utc.public_validity_window["start"] == cairo.public_validity_window["start"]


def test_finalize_b10_shareable_surface_fail_closed_on_expired():
    body = {
        "launch_item_id": 44,
        "success": True,
        "certificate": {"certificate_hash": "abc", "content_age_ms": 700_000},
    }
    out = finalize_b10_shareable_surface(body, payload={})
    assert out["success"] is False
    assert out["presented_as_current"] is False
    assert out["error"] == "share_content_stale"
    assert out["b10_isolation_leakage"] == 0


def test_out_of_scope_launch_noop():
    body = {"launch_item_id": 47, "success": True}
    out = finalize_b10_shareable_surface(body, payload={})
    assert "shareable_public_timing" not in out


@pytest.mark.asyncio
async def test_shareable_decision_card_includes_b10_timing():
    from launch57.trust_batch2 import shareable_decision_card

    out = await shareable_decision_card(
        symbol="BTC",
        params={"decision_action": "WAIT", "decision_sentence": "BTC: wait"},
    )
    assert out["launch_item_id"] == 44
    assert out["b10_shareable_public_timing"]["activated"] is True
    assert out["shareable_public_timing"]["presented_as_current"] is True
    assert out["b10_temporal_owner"] == "launch57.shareable_public_timing_common"


@pytest.mark.asyncio
async def test_shareable_accuracy_page_includes_b10_timing(monkeypatch):
    from launch57.trust_batch2 import shareable_accuracy_page

    monkeypatch.setattr(
        "oracle_track_record.public_track_record",
        lambda: {"cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 68.0}},
    )
    out = await shareable_accuracy_page(symbol="BTC", params={})
    assert out["launch_item_id"] == 45
    assert out["shareable_public_timing"]["publication_time"]
    assert out["b10_isolation_leakage"] == 0


@pytest.mark.asyncio
async def test_guest_trust_surface_includes_b10_timing(monkeypatch):
    from launch57.trust_batch2 import guest_trust_surface

    monkeypatch.setattr(
        "governance.anonymous_visitor_governance.anonymous_visitor_status",
        lambda: {"anonymous_state": "anonymous", "no_pii_leak": True},
    )
    out = await guest_trust_surface(symbol="BTC", params={})
    assert out["launch_item_id"] == 46
    assert out["shareable_public_timing"]["presented_as_current"] is True


def test_shareable_public_timing_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "shareable_public_timing_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
