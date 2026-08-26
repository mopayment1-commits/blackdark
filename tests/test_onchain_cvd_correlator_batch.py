"""Tests — #518 Bucketed CVD, #519 Price-Move Event Correlator, #520 Cost Basis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import bucketed_cvd as bcvd
from bd_platform import cost_basis_distribution as cbd
from bd_platform import price_move_event_correlator as pmec


@pytest.fixture
def cvd_seed(tmp_path, monkeypatch):
    p = tmp_path / "bucketed_cvd_seed.json"
    p.write_text(json.dumps({
        "bucket_definitions": {
            "version": "1.0",
            "buckets": [
                {"id": "retail", "label": "Retail", "min_usd": 0, "max_usd": 10000},
                {"id": "whale", "label": "Whale", "min_usd": 100000, "max_usd": None},
            ],
        },
        "assets": {
            "BTC": {
                "trades": [
                    {"side": "buy", "size_usd": 5000},
                    {"side": "sell", "size_usd": 3000},
                    {"side": "buy", "size_usd": 150000},
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(bcvd, "_SEED_PATH", p)
    return p


@pytest.fixture
def correlator_seed(tmp_path, monkeypatch):
    p = tmp_path / "price_move_event_correlator_seed.json"
    p.write_text(json.dumps({
        "candles": {
            "test_candle": {
                "asset": "BTC", "timestamp": "2026-08-26T14:00:00Z",
                "open": 100, "close": 105, "price_change_pct": 5.0,
            },
        },
        "events": {
            "BTC": [{
                "event_type": "whale_transfer",
                "description": "Wallet moved $10M",
                "timestamp": "2026-08-26T14:02:00Z",
                "source": "onchain", "evidence_id": "ev_001",
            }],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pmec, "_SEED_PATH", p)
    return p


@pytest.fixture
def cost_basis_seed(tmp_path, monkeypatch):
    p = tmp_path / "cost_basis_distribution_seed.json"
    p.write_text(json.dumps({
        "cohort_rules": {"version": "1.0", "rules": ["no_future_price_data"]},
        "assets": {
            "BTC": {
                "as_of": "2026-08-26T00:00:00Z",
                "current_price": 65000,
                "no_future_leakage": True,
                "holders": [
                    {"balance": 100, "acquisition_price": 30000},
                    {"balance": 50, "acquisition_price": 70000},
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(cbd, "_SEED_PATH", p)
    return p


def test_518_bucketed_cvd_integrated(cvd_seed):
    panel = bcvd.build_bucketed_cvd_panel("BTC")
    assert panel["standalone_rejected"] is True
    assert panel["bucket_definitions"]["definitions_documented"] is True
    assert panel["bucket_definitions"]["versioned"] is True
    assert "retail" in panel["summary"]["retail_whale_display"].lower()
    assert panel["rule_based_only"] is True


def test_518_bucket_definitions_versioned(cvd_seed):
    defs = bcvd.build_bucket_definitions()
    assert defs["bucket_version"] == "1.0"
    assert len(defs["buckets"]) >= 2
    retail = next(b for b in defs["buckets"] if b["id"] == "retail")
    assert retail["max_usd"] == 10000


def test_519_renamed_temporal_correlation_not_causation(correlator_seed):
    panel = pmec.build_price_move_event_correlator_panel(candle_id="test_candle")
    assert panel["title"] == "Price-Move Event Correlator"
    assert panel["not_investigator"] is True
    assert panel["temporal_correlation_only"] is True
    assert panel["not_causation"] is True
    event = panel["events_in_same_window"][0]
    assert event["not_causation"] is True
    assert event["causation_unverified"] is True
    assert "causation unverified" in event["display"].lower()


def test_519_linguistic_framing(correlator_seed):
    panel = pmec.build_price_move_event_correlator_panel(candle_id="test_candle")
    framing = panel["linguistic_framing"]
    assert "Events in same window" in framing["use"]
    assert "Cause" in framing["forbidden"]
    assert "unverified" in panel["summary_display"].lower()


def test_520_cost_basis_no_future_leakage(cost_basis_seed):
    panel = cbd.build_cost_basis_panel("BTC")
    assert panel["standalone_rejected"] is True
    assert panel["no_future_leakage"] is True
    assert panel["point_in_time_reproducibility"] is True
    assert "distribution_hash" in panel
    assert panel["cohort_rules"]["no_future_leakage"] is True
    assert panel["cohort_rules"]["cohort_rules_documented"] is True


def test_520_key_levels_descriptive_only(cost_basis_seed):
    panel = cbd.build_cost_basis_panel("BTC")
    for level in panel["key_levels"]:
        assert level["not_support_resistance_prediction"] is True
        assert level["descriptive_only"] is True


def test_api_routes(cvd_seed, correlator_seed, cost_basis_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/bucketed-cvd/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/bucketed-cvd?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/price-move-correlator/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/price-move-correlator?candle_id=test_candle").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/cost-basis/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/cost-basis?asset=BTC").status_code == 200


def test_full_seeds_exist():
    cvd = json.loads(Path("data/bucketed_cvd_seed.json").read_text())
    assert cvd["feature_id"] == 518
    assert cvd["standalone_rejected"] is True

    corr = json.loads(Path("data/price_move_event_correlator_seed.json").read_text())
    assert corr["feature_id"] == 519
    assert "Investigator" in corr["renamed_from"]

    cbd_data = json.loads(Path("data/cost_basis_distribution_seed.json").read_text())
    assert cbd_data["feature_id"] == 520
    assert cbd_data["standalone_rejected"] is True
