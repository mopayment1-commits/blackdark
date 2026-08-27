"""Tests — #777 Evidence & Confidence middleware, #779 MTF Validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import evidence_confidence_middleware as ecm
from bd_platform import mtf_validation_layer as mtf
from bd_platform import signal_validation_layer as svl


@pytest.fixture
def ec_seed():
    return json.loads(Path("data/evidence_confidence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def mtf_seed():
    return json.loads(Path("data/mtf_validation_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def svl_seed():
    return json.loads(Path("data/signal_validation_layer_seed.json").read_text(encoding="utf-8"))


# --- #777 ---


def test_777_middleware_status():
    status = ecm.evidence_confidence_status()
    assert status["feature_id"] == 777
    assert status["cross_cutting"] is True
    assert status["standalone"] is False
    assert "source" in status["mandatory_fields"]


def test_777_enrich_insight_has_metadata(ec_seed):
    payload = ecm.enrich_insight_payload(
        {"asset": "BTC", "confidence_pct": 85},
        system="oracle_api",
        endpoint="/api/oracle/price",
        source_tier="oracle_api",
        age_seconds=120,
    )
    ec = payload["evidence_confidence_777"]
    assert ec["source"]["api_name"] == "oracle_api"
    assert ec["source"]["quality_score"] == 5
    assert "دقيقة" in ec["freshness"]["display_ar"]
    assert len(ec["provenance_chain"]) >= 2
    assert ec["no_black_box"] is True


def test_777_quality_score_tiers():
    assert ecm.resolve_quality_score("tier1_exchange") == 5
    assert ecm.resolve_quality_score("social") == 2


def test_777_asset_card_badge(ec_seed):
    badge = ecm.build_asset_card_evidence_badge_777(
        {"asset": "ETH", "confidence_pct": 70},
        seed=ec_seed,
    )
    assert badge["badge_ar"] == "المصدر والثقة"
    assert badge["quality_score"] == 4


def test_777_report_footer(ec_seed):
    insight = ecm.enrich_insight_payload(
        {"title": "test"},
        system="market_radar",
        endpoint="/panel",
        source_tier="market_radar",
    )
    footer = ecm.build_report_evidence_footer_777([insight])
    assert footer["footer_ar"] == "المصادر + الطوابع الزمنية"
    assert footer["source_count"] >= 1


def test_777_signal_evidence_trail():
    trail = ecm.build_signal_card_evidence_trail_777(
        {"validation_status": "Mixed", "confidence_pct": 67}
    )
    assert trail["panel_ar"] == "تتبع الأدلة"
    assert trail["evidence"]["rule_based_confidence"] is True


def test_777_daily_audit(ec_seed):
    audit = ecm.run_evidence_confidence_audit_777(seed=ec_seed)
    assert audit["audit_sample_size"] == 100
    assert audit["all_passed"] is True


def test_777_integrated_in_signal_validation(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    assert "evidence_confidence_777" in panel
    assert panel["evidence_confidence_777"]["source"]["api_name"] == "signal_engine"


# --- #779 ---


def test_779_mtf_moderate_verdict(mtf_seed):
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=mtf_seed)
    assert panel["ok"] is True
    assert panel["mtf_verdict"] == "Moderate"
    assert panel["agreeing_timeframes"] == 2
    assert panel["confidence_pct"] == pytest.approx(66.7, abs=0.1)


def test_779_three_timeframes_explicit(mtf_seed):
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=mtf_seed)
    assert panel["timeframes"] == ["1H", "4H", "1D"]
    assert len(panel["timeframe_signals"]) == 3


def test_779_rule_version_visible(mtf_seed):
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=mtf_seed)
    assert panel["rule_version_not_hideable"] is True
    assert "MTF Logic v1.0" in panel["rule_documentation"]


def test_779_no_future_candles_block(mtf_seed):
    blocked_seed = dict(mtf_seed)
    cfg = dict(blocked_seed["mtf_validation_779"])
    assets = dict(cfg["assets"])
    btc = dict(assets["BTC"])
    tfs = dict(btc["timeframes"])
    tfs["1H"] = {**tfs["1H"], "future_candle_blocked": True}
    btc["timeframes"] = tfs
    assets["BTC"] = btc
    cfg["assets"] = assets
    blocked_seed["mtf_validation_779"] = cfg
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=blocked_seed)
    assert panel["mtf_verdict"] == "Blocked"


def test_779_confidence_formula(mtf_seed):
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=mtf_seed)
    assert panel["rule_based_confidence"] is True
    assert panel["no_ai_consensus"] is True
    assert "agreeing_timeframes / 3" in panel["confidence_formula"]


def test_779_signal_card_panel(mtf_seed):
    card = mtf.build_signal_card_mtf_panel_779("BTC", seed=mtf_seed)
    assert card["panel_title_ar"] == "التحقق متعدد الأطر"
    assert len(card["timeframe_badges"]) == 3
    assert card["verdict_badge"] == "Moderate"


def test_779_backtest_required(mtf_seed):
    bt = mtf.run_mtf_backtest_779(seed=mtf_seed)
    assert bt["backtest_required"] is True
    assert bt["ok"] is True
    assert bt["backtest_window_days"] == 90


def test_779_alignment_tests(mtf_seed):
    qa = mtf.run_mtf_alignment_tests_779(seed=mtf_seed)
    assert qa["all_passed"] is True


def test_779_evidence_middleware_attached(mtf_seed):
    panel = mtf.build_mtf_validation_panel_779("BTC", seed=mtf_seed)
    assert "evidence_confidence_777" in panel


def test_779_combined_signal_card(svl_seed, mtf_seed):
    card = svl.build_signal_card_combined_validation_776_779(
        "BTC",
        seed=svl_seed,
        mtf_seed=mtf_seed,
    )
    assert card["ok"] is True
    assert 776 in card["feature_refs"]
    assert 779 in card["feature_refs"]
    assert 777 in card["feature_refs"]
    assert card["evidence_trail_777"]["panel_ar"] == "تتبع الأدلة"


def test_779_api_routes(mtf_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/signals/mtf/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/signals/mtf?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["mtf_verdict"] == "Moderate"


def test_777_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/evidence-layer/status").status_code == 200
    audit = c.get("/api/platform/intelligence-ledger/evidence-layer/audit")
    assert audit.status_code == 200
    assert audit.json()["all_passed"] is True
