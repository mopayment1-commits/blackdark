"""Tests — Investor Intelligence Layer epic #562 #563."""

from __future__ import annotations

import json

import pytest

from bd_platform import investor_intelligence_layer as iil


@pytest.fixture
def investor_seed(tmp_path, monkeypatch):
    p = tmp_path / "investor_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "dedupe_map": {"investor_alt": "investor_main"},
        "investors": {
            "investor_main": {
                "name": "Test VC",
                "investor_type": "vc",
                "geography": "US",
                "provenance": {
                    "source": "test_api",
                    "as_of": "2026-08-26T00:00:00Z",
                    "confidence": "high",
                },
            },
            "investor_alt": {
                "name": "Test VC Alt",
                "investor_type": "vc",
                "provenance": {"source": "manual", "confidence": "medium"},
            },
        },
        "rounds": [
            {
                "round_id": "r1",
                "project": "Project A",
                "sector": "DeFi",
                "stage": "Seed",
                "geography": "US",
                "announcement_date": "2025-01-01",
                "investors": [
                    {
                        "investor_id": "investor_main",
                        "amount_usd": 1000000,
                        "evidence_ref": "test:ev-001",
                        "inferred": False,
                    },
                ],
            },
            {
                "round_id": "r2",
                "project": "Project B",
                "sector": "Infrastructure",
                "stage": "Series A",
                "geography": "EU",
                "announcement_date": "2025-06-01",
                "investors": [
                    {
                        "investor_id": "investor_main",
                        "amount_usd": 5000000,
                        "evidence_ref": None,
                        "inferred": True,
                    },
                ],
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(iil, "_SEED_PATH", p)
    return p


def test_epic_status(investor_seed):
    status = iil.investor_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert set(status["feature_ids"]) == {562, 563}


def test_entity_dedupe(investor_seed):
    investors, dedup = iil.dedupe_investors(
        {"investor_main": {}, "investor_alt": {}},
        {"investor_alt": "investor_main"},
    )
    assert dedup["entity_dedupe"] is True
    assert dedup["deduped_count"] == 1


def test_source_provenance(investor_seed):
    intel = iil.build_investor_intelligence("investor_main")
    assert intel["provenance"]["source_provenance"] is True
    assert intel["provenance"]["confidence"] == "high"


def test_no_inferred_affiliation_flagged(investor_seed):
    intel = iil.build_investor_intelligence("investor_main")
    inferred = [a for a in intel["affiliations"] if a.get("inferred")]
    assert len(inferred) == 1
    assert inferred[0]["affiliation_documented"] is False


def test_investor_profiles(investor_seed):
    profile = iil.build_investor_profiles_panel("investor_main")
    assert profile["ok"] is True
    assert len(profile["portfolio"]) == 2
    assert profile["activity_breakdown"]["round_count"] == 2


def test_main_panel(investor_seed):
    panel = iil.build_investor_intelligence_panel(investor_id="investor_main")
    assert panel["ok"] is True
    assert "562_investor_intelligence" in panel["sub_modules"]
    assert "563_investor_profiles" in panel["sub_modules"]


def test_reconciliation_tests(investor_seed):
    result = iil.run_reconciliation_tests()
    assert result["all_passed"] is True
