"""Tests — Feature #250 Historical Narrative Explorer."""

from __future__ import annotations

import json

import pytest

from bd_platform import historical_narrative_explorer as hne


@pytest.fixture
def narrative_seed(tmp_path, monkeypatch):
    p = tmp_path / "historical_narrative_explorer_seed.json"
    p.write_text(json.dumps({
        "dataset": {
            "version": "3.1",
            "social_source": "Twitter/X API v2",
            "price_source": "Oracle API",
            "coverage_start": "2020-01-01",
            "coverage_end": "2026-08-25",
            "last_updated": "2026-08-25",
        },
        "versions": [{"version": "3.1", "effective_at": "2026-08-01"}],
        "narratives": {
            "defi_summer": {
                "name": "DeFi Summer",
                "keyword": "DeFi Summer",
                "default_asset": "ETH",
                "default_time_range": "2020-06 to 2020-09",
                "historical_sample": "2020-06 to 2020-09",
                "narrative_peak_utc": "2020-06-15T14:00:00Z",
                "price_peak_utc": "2020-09-01T09:00:00Z",
                "lag_hours": 1848,
                "alignment_verified": True,
                "price_change_pct": 340.0,
                "extraction": {
                    "method": "TF-IDF + manual curation",
                    "spam_filtered": True,
                    "bot_excluded": True,
                },
                "correlation": {
                    "value_90d": 0.78,
                    "regime": "Risk-On",
                    "historical_range": "0.2-0.8",
                    "interpretation": "Strong positive relationship",
                },
                "thesis_integration": {
                    "example": "DeFi Summer drove ETH +340%",
                },
                "trending_integration": {
                    "current_trending": "RWA",
                    "historical_similar": "DeFi Summer",
                    "pattern_match_pct": 68,
                },
                "timeline": [{"date": "2020-06-01", "narrative_volume": 1200, "price_usd": 240}],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(hne, "_SEED_PATH", p)
    return p


def test_status_sprint2_intelligence(narrative_seed):
    status = hne.historical_narrative_explorer_status()
    assert status["feature_id"] == 250
    assert status["sprint"] == 2
    assert status["sentiment_research_only"] is True
    assert status["disclaimer_non_hideable"] is True


def test_no_causation_claim(narrative_seed):
    block = hne.build_no_causation_block(0.65, 72)
    assert block["no_causation_claim"] is True
    assert block["correlation_not_causation"] is True
    assert "Correlation ≠ Causation" in block["display"]


def test_timestamps_aligned(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    alignment = hne.build_timestamp_alignment(narrative)
    assert alignment["timestamps_aligned"] is True
    assert alignment["alignment_verified"] is True
    assert "Alignment verified: Yes" in alignment["display"]


def test_historical_data_version_preserved(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    dataset = hne.build_dataset_version_block(seed)
    assert dataset["historical_data_preserved"] is True
    assert dataset["no_overwrite"] is True
    assert dataset["dataset_version"] == "3.1"


def test_lead_lag_documented(narrative_seed):
    method = hne.build_lead_lag_methodology()
    assert method["documented"] is True
    assert method["no_magic_lag"] is True
    assert "xcorr" in method["method"].lower()


def test_narrative_extraction_transparent(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    extraction = hne.build_narrative_extraction_block(narrative)
    assert extraction["spam_filtered"] is True
    assert extraction["bot_excluded"] is True
    assert "TF-IDF" in extraction["display"]


def test_correlation_descriptive_only(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    corr = hne.build_correlation_view(narrative)
    assert corr["descriptive_only"] is True
    assert corr["no_buy_signals"] is True
    assert corr["no_causation_claim"] is True


def test_explorer_ux_no_prescriptive(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    ux = hne.build_explorer_ux_block("defi_summer", narrative)
    assert ux["user_explores_not_answers"] is True
    assert ux["no_prescriptive_output"] is True


def test_thesis_workspace_integration(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    thesis = hne.build_thesis_workspace_integration(narrative)
    assert thesis["thesis_workspace_feature_id"] == 756
    assert thesis["add_to_thesis_supported"] is True


def test_trending_words_integration(narrative_seed):
    seed = json.loads(narrative_seed.read_text(encoding="utf-8"))
    narrative = seed["narratives"]["defi_summer"]
    trending = hne.build_trending_words_integration(narrative)
    assert trending["trending_words_feature_id"] == 758
    assert trending["past_not_future"] is True
    assert "Past ≠ Future" in trending["display"]


def test_no_opportunity_alerts(narrative_seed):
    policy = hne.build_alert_policy()
    assert policy["buy_signal_alerts_forbidden"] is True
    assert policy["sentiment_research_only"] is True
    assert policy["no_yield_arbitrage"] is True


def test_panel_full_explorer(narrative_seed):
    panel = hne.build_historical_narrative_panel(narrative_id="defi_summer")
    assert panel["ok"] is True
    assert panel["answers_what_happened_not_what_will"] is True
    assert panel["explorer"]["no_causation"]["no_causation_claim"] is True
    assert panel["acceptance_criteria"]["disclaimer_non_hideable"] is True


def test_historical_qa_tests(narrative_seed):
    tests = hne.run_historical_qa_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["historical_qa_tests"]]
    assert "no_causation_claim" in test_names
    assert "no_opportunity_alerts" in test_names
    assert "timestamps_aligned_defi_summer" in test_names


def test_api_routes(narrative_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get(
        "/api/platform/intelligence-ledger/intelligence-layer/historical-narratives/status"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/intelligence-layer/historical-narratives?narrative_id=defi_summer"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/intelligence-layer/historical-narratives/historical-qa"
    ).status_code == 200
