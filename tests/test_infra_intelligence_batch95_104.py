"""Tests — Infrastructure & Intelligence (#95–#104)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infra_intelligence_layer as infra


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    infra.reset_infra_intelligence_state()
    yield
    infra.reset_infra_intelligence_state()


def test_95_usage_analytics(seed):
    infra.track_usage_event_95(endpoint="/api/oracle", seed=seed)
    dash = infra.build_admin_analytics_dashboard_95(seed=seed)
    assert dash["internal_only"] is True
    assert dash["summary"]["total_events"] >= 1


def test_96_streaming_stack(seed):
    status = infra.streaming_stack_status_96(seed=seed)
    assert status["ai_training"] == "deferred"
    queued = infra.enqueue_stream_event_96(source="oracle", seed=seed)
    assert queued["queued"] is True


def test_97_flywheel(seed):
    fb = infra.submit_insight_feedback_97(insight_id="x1", feedback="hit", seed=seed)
    assert fb["feedback_recorded"] is True
    assert "weights" in fb


def test_98_signal_registry(seed):
    reg = infra.register_canonical_signal_98(
        name="MACD", formula="EMA(12)-EMA(26)", data_source="ta", seed=seed
    )
    assert reg["ok"] is True
    dup = infra.register_canonical_signal_98(
        name="MACD_COPY", formula="EMA(12)-EMA(26)", data_source="other", seed=seed
    )
    assert dup.get("blocked") is True


def test_99_sybil_filter(seed):
    wallets = [
        {"wallet_id": "a", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "b", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "c", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
    ]
    result = infra.filter_sybil_clusters_99(wallets, seed=seed)
    assert result["excluded_count"] >= 3


def test_100_liquidation_proximity(seed):
    from bd_platform.whales_institutional_layer import evaluate_liquidation_alert_82

    liq = evaluate_liquidation_alert_82(price=63000, liquidation_level=62000, seed=seed)
    assert "proximity_pct" in liq
    assert liq["merged_features"] == [82, 100]


def test_101_oracle_freshness(seed):
    fresh = infra.validate_oracle_freshness_101(
        primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_000_100, seed=seed
    )
    assert fresh["accepted"] is True
    stale = infra.validate_oracle_freshness_101(
        primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_020_000, seed=seed
    )
    assert stale["accepted"] is False


def test_102_il_vulnerability(seed):
    il = infra.compute_il_vulnerability_102(seed=seed)
    assert 0 <= il["vulnerability_score"] <= 100
    assert "formula" in il


def test_103_drawdown_duration(seed):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    risk = build_advanced_risk_report_77(
        [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}],
        price_history=[
            {"date": "2026-01-01", "value_usd": 120000},
            {"date": "2026-02-01", "value_usd": 80000},
            {"date": "2026-03-01", "value_usd": 100000},
        ],
        seed=seed,
    )
    assert "drawdown_lifecycle" in risk
    assert risk["drawdown_lifecycle"]["max_drawdown_pct"] > 0


def test_104_leverage_overhang(seed):
    overhang = infra.compute_leverage_overhang_104(seed=seed)
    assert overhang["overhang_factor"] > 0
    assert overhang["fragility"] in ("red", "yellow", "green")


def test_infra_intelligence_e2e(seed):
    assert infra.run_infra_intelligence_e2e_95_104(seed=seed)["all_passed"] is True
