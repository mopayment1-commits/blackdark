"""Tests for pentagonal template + six-hero binding deliverable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pentagonal_template() -> dict:
    path = ROOT / "docs" / "PENTAGONAL_TEMPLATE_1_100.json"
    if not path.exists():
        pytest.skip("Run scripts/generate_pentagonal_hero_binding_report.py first")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def hero_report() -> dict:
    path = ROOT / "docs" / "HERO_SIX_BINDING_REPORT.json"
    if not path.exists():
        pytest.skip("Run scripts/generate_pentagonal_hero_binding_report.py first")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def closure_report() -> dict:
    path = ROOT / "docs" / "PENTAGONAL_HERO_CLOSURE_REPORT.json"
    if not path.exists():
        pytest.skip("Run scripts/generate_pentagonal_hero_binding_report.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def test_pentagonal_row_count_100(pentagonal_template: dict) -> None:
    assert pentagonal_template["row_count"] == 100
    assert len(pentagonal_template["rows"]) == 100


def test_pentagonal_checksum_valid(pentagonal_template: dict) -> None:
    rows = pentagonal_template["rows"]
    canonical = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert pentagonal_template["checksum_sha256"] == expected


def test_pentagonal_ids_1_to_100(pentagonal_template: dict) -> None:
    ids = [r["capability_id"] for r in pentagonal_template["rows"]]
    assert ids == list(range(1, 101))


def test_pentagonal_has_e2e_samples(pentagonal_template: dict) -> None:
    for row in pentagonal_template["rows"]:
        assert "actual_e2e_sample" in row["internal_goal"]


def test_ai_drift_column_present(pentagonal_template: dict) -> None:
    ai_ids = {24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 66, 69, 99, 100}
    for row in pentagonal_template["rows"]:
        cid = row["capability_id"]
        if cid in ai_ids:
            assert row["ai_drift_status"] == "MONITORED"
            assert "psi_status" in row
        else:
            assert row["ai_drift_status"] == "N/A"


def test_ai_psi_table_has_16_rows(pentagonal_template: dict) -> None:
    table = pentagonal_template.get("ai_psi_table") or []
    assert len(table) == 16


def test_six_heroes_present(hero_report: dict) -> None:
    expected = {
        "Single-Sentence Oracle",
        "Public Accuracy Ledger",
        "Arbitrage Scanner",
        "Whale Signal vs Noise",
        "Stealth Advisor",
        "B2B Feed",
    }
    assert set(hero_report["heroes"]) == expected
    assert len(hero_report["hero_sections"]) == 6


def test_hero_binding_checksum(hero_report: dict) -> None:
    rows = []
    for section in hero_report["hero_sections"]:
        rows.extend(section["1_feed_map"])
    canonical = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert hero_report["binding_checksum_sha256"] == expected


def test_hero_feeds_scope_1_100(hero_report: dict) -> None:
    for section in hero_report["hero_sections"]:
        for feed in section["1_feed_map"]:
            assert 1 <= feed["capability_id"] <= 100


def test_lookahead_all_pass(hero_report: dict) -> None:
    summary = hero_report["lookahead_summary"]
    assert summary["failed"] == 0
    assert summary["passed"] == summary["total_caps_checked"]


def test_closure_report_items_1_21(closure_report: dict) -> None:
    required = [
        "item_01_ai_capabilities_psi",
        "item_01_psi_methodology_correction",
        "item_04_unbound_capabilities",
        "item_04b_b2b_key_comparison",
        "item_05_get_entitlement_doc_status",
        "item_08_live_verification_table",
        "item_10_lookahead_60_vs_81",
        "item_11_lookahead_time_distribution",
        "item_15_self_resolve_checksum",
        "item_18_outlier_prevention_per_hero",
        "item_21_transparency_code_per_hero",
    ]
    for key in required:
        assert key in closure_report


def test_psi_methodology_corrected(closure_report: dict) -> None:
    psi = closure_report["item_01_psi_methodology_correction"]
    assert psi.get("measured") is True
    assert psi.get("verdict", "").startswith("MEASUREMENT_ERROR_CORRECTED")
    assert psi.get("predict_direction_frozen") is False
    assert psi["platform_max_psi"] < 2.0  # not the bogus 11.1065
    assert psi["methodology"]["invalid_prior_max_psi"] > 10.0
    assert psi["caps_66_69_assessment"]["prior_was_measurement_error"] is True


def test_lookahead_has_real_deltas(closure_report: dict) -> None:
    dist = closure_report["item_11_lookahead_time_distribution"]
    assert dist["samples_with_delta"] > 0
    assert dist["caps_with_nested_timestamps"] > 0
    assert dist["median_seconds"] is not None


def test_loo_true_methodology(hero_report: dict) -> None:
    total = sum(s["8_stability_test"].get("loo_test_count", 0) for s in hero_report["hero_sections"])
    assert total > 30  # expanded: 5 scenarios × each input cap per hero
    for section in hero_report["hero_sections"]:
        for test in section["8_stability_test"]["loo_tests"]:
            assert test["exclusions_count"] == 1


def test_shared_dependency_risk(closure_report: dict) -> None:
    risk = closure_report["item_06_namespace_independence"]["shared_dependency_risk"]
    assert "Whale Signal vs Noise" in risk["affected_heroes"]
    assert "B2B Feed" in risk["affected_heroes"]
    assert risk["shared_module"] == "whale_tracker.py"


def test_get_entitlement_doc_not_modified(closure_report: dict) -> None:
    doc = closure_report["item_05_get_entitlement_doc_status"]
    assert doc["exists"] is True
    assert doc["modified_for_wording_correction"] is False


def test_supplemental_closure_report() -> None:
    path = ROOT / "docs" / "SUPPLEMENTAL_CLOSURE_REPORT_1_18.json"
    assert path.exists()
    report = json.loads(path.read_text())
    assert report["item_07_mece_unbound_40"]["pairs_total"] == 3180
    assert report["item_07_mece_unbound_40"]["counts"]["DUPLICATE-CONFIRMED"] == 0
    assert report["item_01_psi_monitor_elevated"]["classification"] == "monitor_elevated"
    assert report["item_16_b2b_awaiting"]["status"] == "AWAITING_OWNER_ACTION"
    assert report["item_17_18_telegram"]["item_17_bot_link_fix"]["bot_username"] == "BLACKDARKAI_oncall_bot"


def test_closure_unbound_count(closure_report: dict) -> None:
    unbound = closure_report["item_04_unbound_capabilities"]
    assert unbound["unique_fed_capability_count"] == 60
    assert unbound["unbound_unique_count"] == 40
    assert unbound["binding_row_count"] == 81


def test_closure_endpoint_substitution_checksum(closure_report: dict) -> None:
    sub = closure_report["item_15_self_resolve_checksum"]
    issues = sub["discovered_issues"]
    canonical = json.dumps(issues, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert sub["checksum_sha256"] == expected


def test_closure_live_paths_production(closure_report: dict) -> None:
    table = closure_report["item_08_live_verification_table"]
    assert len(table) == 6
    for row in table:
        assert row["path_type"] == "production_real"
        assert row["live_ok"] is True


def test_prior_issues_no_hash_prefix(closure_report: dict) -> None:
  # item 17 encoding fix verified in hero report
    issues = [i["issue"] for i in closure_report["item_15_self_resolve_checksum"]["discovered_issues"]]
    assert all("#" not in i or "403" in i for i in issues)


@pytest.mark.asyncio
async def test_local_hero_endpoints() -> None:
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    endpoints = [
        "/api/whale/signal-vs-noise",
        "/api/oracle/audit-chain/verify",
        "/api/oracle/net-edge-truth",
        "/api/oracle/data-hub/BTC",
        "/api/ledger/share-kit",
    ]
    for path in endpoints:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    stealth = client.post("/api/whale/stealth-advisor", json={"asset": "BTC", "notional_usd": 5000})
    assert stealth.status_code == 200
