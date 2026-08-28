"""Tests — Data Freshness Badge (#1030 Cross-Cutting UI)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bd_platform.data_freshness_badge import (
    attach_freshness_to_response,
    check_component_gate_1030,
    compute_freshness_state,
    freshness_badge_status_1030,
    freshness_from_response_metadata,
    render_badge_html,
    run_freshness_badge_e2e_1030,
)


@pytest.fixture
def dfb_seed() -> dict:
    return json.loads(Path("data/data_freshness_badge_seed.json").read_text(encoding="utf-8"))


def test_1030_status_no_standalone(dfb_seed):
    status = freshness_badge_status_1030(seed=dfb_seed)
    assert status["standalone_rejected"] is True
    assert len(status["states"]) == 5


def test_live_state(dfb_seed):
    now = datetime.now(UTC)
    result = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        source="binance",
        now=now,
        seed=dfb_seed,
    )
    assert result["state"] == "Live"
    assert result["confidence"] == "High"
    assert result["expected_interval_ms"] == 300_000


def test_delayed_state(dfb_seed):
    now = datetime.now(UTC)
    old = now - timedelta(minutes=7)
    result = compute_freshness_state(
        category="price",
        timestamp=old.isoformat(),
        source="binance",
        now=now,
        seed=dfb_seed,
    )
    assert result["state"] == "Delayed"
    assert result["confidence"] == "Medium"


def test_recovered_state(dfb_seed):
    now = datetime.now(UTC)
    result = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        recovered=True,
        recovered_from="coingecko",
        now=now,
        seed=dfb_seed,
    )
    assert result["state"] == "Recovered"
    assert result["source"] == "coingecko"


def test_stabilized_and_provisional(dfb_seed):
    now = datetime.now(UTC)
    stab = compute_freshness_state(category="price", timestamp=now.isoformat(), stabilized=True, now=now, seed=dfb_seed)
    prov = compute_freshness_state(category="price", timestamp=now.isoformat(), provisional=True, now=now, seed=dfb_seed)
    assert stab["state"] == "Stabilized"
    assert prov["state"] == "Provisional"


def test_iso8601_timestamp_required(dfb_seed):
    now = datetime.now(UTC)
    result = compute_freshness_state(category="price", timestamp=now.isoformat(), now=now, seed=dfb_seed)
    assert "+00:00" in result["timestamp"]
    assert result["relative_supplement"]


def test_outlier_review_combined(dfb_seed):
    now = datetime.now(UTC)
    result = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        outlier_detected=True,
        now=now,
        seed=dfb_seed,
    )
    assert result["outlier_review"] is True
    assert "Outlier Review" in result["badge"]["label"]


def test_freshness_from_gap_recovery_metadata(dfb_seed):
    payload = {
        "recovered": True,
        "badge": "Recovered from coingecko",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    result = freshness_from_response_metadata(payload, category="price", seed=dfb_seed)
    assert result["state"] == "Recovered"


def test_attach_freshness_to_response(dfb_seed):
    now = datetime.now(UTC).isoformat()
    out = attach_freshness_to_response({"value": 42000}, category="price", source="binance", timestamp=now, seed=dfb_seed)
    assert "freshness" in out
    assert out["freshness"]["source"] == "binance"
    assert "actual_delay_ms" in out["freshness"]
    assert out["freshness"]["fee_db"]["fee_db_logged"] is True


def test_badge_html_render(dfb_seed):
    now = datetime.now(UTC)
    fresh = compute_freshness_state(category="price", timestamp=now.isoformat(), source="binance", now=now, seed=dfb_seed)
    html = render_badge_html(fresh)
    assert "data-freshness-badge" in html
    assert "binance" in html
    assert "dfb-live" in html


def test_volume_threshold(dfb_seed):
    now = datetime.now(UTC)
    result = compute_freshness_state(category="volume", timestamp=now.isoformat(), now=now, seed=dfb_seed)
    assert result["expected_interval_ms"] == 3_600_000


def test_component_gate(dfb_seed):
    gate = check_component_gate_1030(seed=dfb_seed)
    assert gate["component_ready"] is True


def test_e2e_all_checks(dfb_seed):
    e2e = run_freshness_badge_e2e_1030(seed=dfb_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
