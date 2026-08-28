"""Tests — Batch 27: #921 AI Provenance, #922 Auto-Report, #923 AML, #924 Export, #926 Entity Layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import ai_output_provenance_policy as prov921
from bd_platform import data_engine_export_layer as export
from bd_platform import onchain_intelligence_extension as onchain
from bd_platform import research_intelligence_portal as rip


@pytest.fixture
def prov921_seed() -> dict:
    return json.loads(Path("data/ai_output_provenance_policy_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def rip_seed() -> dict:
    return json.loads(Path("data/research_intelligence_portal_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def export_seed() -> dict:
    return json.loads(Path("data/data_engine_export_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_rip():
    rip.reset_research_portal_state()
    yield
    rip.reset_research_portal_state()


# --- #921 ---


def test_921_policy_status(prov921_seed):
    status = prov921.ai_provenance_policy_status_921(seed=prov921_seed)
    assert status["standalone_rejected"] is True
    assert status["cross_cutting"] is True
    assert status["fails_closed"] is True


def test_921_claim_classification():
    fact = prov921.classify_claim("BTC price is 64800", evidence=[{"source": "market"}])
    assert fact["claim_type"] == "fact"
    assert fact["grounded"] is True

    no_ev = prov921.classify_claim("BTC price is 64800", evidence=[])
    assert no_ev["claim_type"] == "unsupported"


def test_921_compliance_footer(prov921_seed):
    output = prov921.attach_compliance_footer_921(
        {"ok": True, "answer": "Test", "citations": [{"source": "data", "timestamp": "2026-08-28"}]},
        feature_ref="919",
        seed=prov921_seed,
    )
    assert output.get("compliance_footer") is not None
    assert output["compliance_footer"]["confidence_score"] > 0


def test_921_fails_closed(prov921_seed):
    blocked = prov921.attach_compliance_footer_921(
        {"ok": True, "claims": [{"claim": "Will moon", "claim_type": "fact", "evidence": []}]},
        feature_ref="920",
        seed=prov921_seed,
    )
    assert blocked.get("blocked") is True


def test_921_regression(prov921_seed):
    reg = prov921.run_ai_provenance_regression_tests_921(seed=prov921_seed)
    assert reg["all_passed"] is True


# --- #922 ---


def test_922_auto_report(rip_seed):
    report = rip.generate_auto_report_922(seed=rip_seed)
    assert report["ok"] is True
    assert report["fact_inference_separated"] is True
    assert report["narrative_matches_underlying"] is True
    assert report.get("compliance_footer") is not None


def test_922_integrated_analyst(rip_seed):
    result = rip.ask_ai_analyst_919("Bitcoin NVT and on-chain activity", seed=rip_seed)
    assert result.get("compliance_footer") is not None


# --- #923 / #926 ---


def test_onchain_extension_status(onchain_seed):
    status = onchain.onchain_extension_status(seed=onchain_seed)
    assert status["standalone_rejected"] is True
    assert status["no_legal_conclusion"] is True


def test_923_aml_screening(onchain_seed):
    screen = onchain.screen_address_923("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert screen["ok"] is True
    assert screen["no_legal_conclusion"] is True
    assert screen["not_money_laundering_detected"] is True
    assert len(screen["indicators"]) >= 3


def test_926_labels(onchain_seed):
    labels = onchain.get_address_labels_926("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert labels["ok"] is True
    assert labels["labels"][0].get("label") == "Binance Hot Wallet"

    unknown = onchain.get_address_labels_926("0x0000000000000000000000000000000000000001", seed=onchain_seed)
    assert unknown["labels"][0]["label"] == "Unknown"


def test_926_cohorts(onchain_seed):
    cohort = onchain.build_address_cohort_926("whale_accumulators", seed=onchain_seed)
    assert cohort["rule_based_only"] is True


def test_onchain_e2e(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True


# --- #924 ---


def test_924_status(export_seed):
    status = export.export_layer_status_924(seed=export_seed)
    assert status["standalone_rejected"] is True
    assert status["api_version"] == "v1"
    assert len(status["formats"]) == 3


def test_924_export(export_seed):
    result = export.export_dataset_924("market_fundamentals", fmt="json", seed=export_seed)
    assert result["ok"] is True
    assert result["checksum_sha256"]
    assert result["contract_tested"] is True


def test_924_contract_tests(export_seed):
    tests = export.run_export_contract_tests_924(seed=export_seed)
    assert tests["all_passed"] is True


def test_924_e2e(export_seed):
    e2e = export.run_export_layer_e2e_924(seed=export_seed)
    assert e2e["all_passed"] is True
