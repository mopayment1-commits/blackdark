"""Tests — #599 Hype vs Reality Signal (merged into #524)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cross_domain_market_context_layer as cdmc
from bd_platform import hype_vs_reality_signal as hvr


@pytest.fixture
def hvr_seed(tmp_path, monkeypatch):
    main = Path("data/hype_vs_reality_signal_seed.json")
    p = tmp_path / "hype_vs_reality_signal_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(hvr, "_SEED_PATH", p)
    return p


# --- #599 classifier ---


def test_599_four_states_classifier():
    assert hvr.classify_hype_vs_reality("rising", "bullish")["state_id"] == "confirmed"
    assert hvr.classify_hype_vs_reality("up", "neutral")["state_id"] == "social_only"
    assert hvr.classify_hype_vs_reality("flat", "rising")["state_id"] == "on_chain_only"
    assert hvr.classify_hype_vs_reality("bullish", "falling")["state_id"] == "contradictory"


def test_599_no_forced_consensus():
    result = hvr.classify_hype_vs_reality("down", "down")
    assert result["state_id"] == "unclassified"
    assert result["no_forced_consensus"] is True


def test_599_badge_structure():
    result = hvr.classify_hype_vs_reality("rising", "rising")
    badge = result["badge"]
    assert badge["emoji"] == "🟢"
    assert badge["label"] == "Confirmed"
    assert badge["show_on_every_signal"] is True


# --- #599 panel ---


def test_599_renamed_not_engine(hvr_seed):
    panel = hvr.build_hype_vs_reality_panel("BTC")
    assert panel["legal_name"] == "Hype vs Reality Signal"
    assert panel["not_engine"] is True
    assert "Engine" not in panel["legal_name"]


def test_599_contributors_freshness_confidence(hvr_seed):
    signal = hvr.build_hype_vs_reality_signal("BTC")
    assert signal["contributors_shown"] is True
    assert signal["freshness_shown"] is True
    assert signal["confidence_shown"] is True
    assert signal["contributors"]["social"]["shown"] is True
    assert signal["contributors"]["onchain"]["shown"] is True


def test_599_historical_validation(hvr_seed):
    signal = hvr.build_hype_vs_reality_signal("BTC")
    hist = signal["historical_validation"]
    assert hist["enabled"] is True
    assert hist["contradictory_correction_rate_pct"] >= 80
    assert hist["display_required"] is True


def test_599_no_advisor(hvr_seed):
    panel = hvr.build_hype_vs_reality_panel("BTC")
    assert panel["no_chatbot_advisor_role"] is True
    assert "buy or sell" in panel["terms_statement"].lower()


def test_599_attach_badge(hvr_seed):
    enriched = hvr.attach_signal_quality_badge({"asset": "BTC", "signal_id": "test"})
    assert "signal_quality_badge" in enriched
    assert enriched["hype_vs_reality_signal_599"]["not_advisory"] is True


def test_599_summary_counts(hvr_seed):
    panel = hvr.build_hype_vs_reality_panel("BTC")
    summary = panel["summary"]
    assert summary["total"] >= 1
    assert "confirmed" in summary["counts"]
    assert "contradictory" in summary["counts"]


def test_599_reconciliation(hvr_seed):
    assert hvr.run_reconciliation_tests()["ok"] is True


# --- #524 integration ---


def test_599_merged_into_524(hvr_seed):
    status = hvr.hype_vs_reality_signal_status()
    assert status["merged_into"] == 524
    assert status["standalone"] is False


def test_524_absorbs_599():
    data = json.loads(Path("data/cross_domain_market_context_layer_seed.json").read_text())
    assert 599 in data["absorbed_tickets"]


def test_524_sub_module_599_in_panel(hvr_seed, monkeypatch):
    main = Path("data/cross_domain_market_context_layer_seed.json")
    p = Path("/tmp/cdmc_test_seed.json")
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cdmc, "_SEED_PATH", p)

    panel = cdmc.build_market_context_panel(context_id="btc_cross_domain")
    feeds = panel["sub_modules"]["feeds"]
    assert "599" in feeds
    assert feeds["599"]["legal_name"] == "Hype vs Reality Signal"


def test_api_routes(hvr_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/hype-vs-reality/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/hype-vs-reality?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-context/sub-module/599").status_code == 200
