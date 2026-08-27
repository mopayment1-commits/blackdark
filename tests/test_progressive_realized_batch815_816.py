"""Tests — #815 Progressive Disclosure, #816 Realized Cap."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml
from ux_mode import (
    apply_progressive_disclosure_815,
    build_asset_card_progressive_disclosure_815,
    build_report_progressive_disclosure_815,
    progressive_disclosure_status_815,
)


@pytest.fixture
def oml_seed() -> dict:
    return json.loads(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"))


# --- #815 ---


def test_815_status():
    status = progressive_disclosure_status_815()
    assert status["standalone_rejected"] is True
    assert status["asset_card_cta_ar"] == "عرض المزيد"
    assert status["report_cta_ar"] == "التفاصيل"
    assert status["complements_feature_ref"] == 804


def test_815_asset_card_collapsed():
    card = build_asset_card_progressive_disclosure_815("BTC", expanded=False)
    assert card["expanded"] is False
    assert card["expand_cta_ar"] == "عرض المزيد"
    assert len(card["collapsed_metrics"]) == 2
    assert card["metrics_hidden_until_expand"] >= 1
    assert "98,500" in card["summary_line"] or "98500" in card["summary_line"]


def test_815_asset_card_expanded():
    card = build_asset_card_progressive_disclosure_815("BTC", expanded=True)
    assert card["expanded"] is True
    assert len(card["collapsed_metrics"]) == len(card["full_metrics"])


def test_815_report_details():
    report = build_report_progressive_disclosure_815(expanded=False)
    assert report["details_cta_ar"] == "التفاصيل"
    assert "summary" in report["visible_content"]

    expanded = build_report_progressive_disclosure_815(expanded=True)
    assert "details" in expanded["visible_content"]


def test_815_apply_pattern():
    out = apply_progressive_disclosure_815(
        {"metrics": [{"key": "price"}, {"key": "nvt"}, {"key": "volume_24h"}]},
        surface="market_radar",
    )
    assert out["basic_info_first"] is True
    assert out["advanced_on_demand"] is True


# --- #816 ---


def test_816_realized_cap_btc(oml_seed):
    suite = oml.build_realized_cap_suite_816("BTC", seed=oml_seed)
    assert suite["ok"] is True
    assert suite["metric_id"] == "realized_cap"
    assert suite["utxo_chains_only"] is True
    assert (suite.get("formula") or {}).get("source") == "CoinMetrics"
    assert "Σ" in (suite.get("formula") or {}).get("expression", "")


def test_816_rejects_eth_account_chain(oml_seed):
    suite = oml.build_realized_cap_suite_816("ETH", seed=oml_seed)
    assert suite["ok"] is False
    assert suite["error"] == "utxo_chains_only"


def test_816_nvt_integration(oml_seed):
    suite = oml.build_realized_cap_suite_816("BTC", seed=oml_seed)
    nvt = suite.get("nvt_integration_761") or {}
    assert nvt.get("enabled") is True
    assert nvt.get("nvt_realized_cap") is not None


def test_816_coinmetrics_qa(oml_seed):
    qa = oml.run_realized_cap_qa_816("BTC", seed=oml_seed)
    assert qa["within_tolerance"] is True
    assert qa["tolerance_pct"] == 2.0


def test_816_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_realized_cap_widget_816("BTC", seed=oml_seed)
    assert widget["widget_label_ar"] == "القيمة المُحققة"


def test_816_asset_card_sparkline(oml_seed):
    card = oml.build_asset_card_realized_cap_sparkline_816("BTC", seed=oml_seed)
    assert card["ok"] is True
    assert len(card["sparkline"]) >= 1


def test_816_market_radar_integration():
    panel = mri.build_market_radar_panel("BTC")
    assert (panel.get("realized_cap_816") or {}).get("ok") is True


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/ux-layer/progressive-disclosure/status").status_code == 200
    card = c.get("/api/platform/intelligence-ledger/ux-layer/progressive-disclosure/asset-card?asset=BTC")
    assert card.status_code == 200
    assert card.json()["expand_cta_ar"] == "عرض المزيد"
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/realized-cap?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/realized-cap?asset=ETH").status_code == 404
