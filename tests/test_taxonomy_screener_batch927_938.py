"""Tests — Batch 28: #927 Taxonomy, #928 Screener, #930/#937 Bridges, #931 Verification, #938 Decision Intelligence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_asset_taxonomy as taxonomy
from bd_platform import intelligence_ledger_decision_intelligence as decision
from bd_platform import market_screener as screener
from bd_platform import onchain_intelligence_extension as onchain
from bd_platform import public_accuracy_verification_engine as verification


@pytest.fixture
def taxonomy_seed() -> dict:
    return json.loads(Path("data/data_engine_asset_taxonomy_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def verification_seed() -> dict:
    return json.loads(Path("data/public_accuracy_verification_engine_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def decision_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_decision_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_verification():
    verification.reset_verification_engine_state()
    yield
    verification.reset_verification_engine_state()


# --- #927 Asset Taxonomy ---


def test_927_taxonomy_status(taxonomy_seed):
    status = taxonomy.asset_taxonomy_status_927(seed=taxonomy_seed)
    assert status["standalone_rejected"] is True
    assert len(status["hierarchy_levels"]) == 4
    assert status["no_silent_remap"] is True


def test_927_versioned_taxonomy(taxonomy_seed):
    v1 = taxonomy.get_taxonomy_version_927("1.0.0", seed=taxonomy_seed)
    v2 = taxonomy.get_taxonomy_version_927("1.1.0", seed=taxonomy_seed)
    assert v1["ok"] is True
    assert v2["ok"] is True
    assert v1["version"] != v2["version"]


def test_927_historical_auditable(taxonomy_seed):
    hist = taxonomy.get_classification_history_927("SOL", seed=taxonomy_seed)
    assert hist["old_classifications_preserved"] is True
    assert len(hist["history"]) >= 1


def test_927_unknown_explicit(taxonomy_seed):
    unknown = taxonomy.get_asset_classification_927("FAKECOIN", seed=taxonomy_seed)
    assert unknown["unknown_remains_unknown"] is True


def test_927_taxonomy_e2e(taxonomy_seed):
    e2e = taxonomy.run_asset_taxonomy_e2e_927(seed=taxonomy_seed)
    assert e2e["all_passed"] is True


# --- #928 Asset Screener ---


def test_928_screener_status():
    status = screener.asset_screener_status_928()
    assert status["standalone_rejected"] is True
    assert status["pagination"] == "cursor_based"
    assert "top_gainers" in status["presets"]


def test_928_backend_filters():
    result = screener.run_asset_screener_928(preset_id="high_volume")
    assert result["ok"] is True
    assert result["backend_enforced"] is True
    assert result["pagination"]["cursor_based"] is True


def test_928_taxonomy_filter():
    result = screener.run_asset_screener_928(sector="layer1")
    assert result["ok"] is True
    symbols = [r["symbol"] for r in result["results"]]
    assert "BTC" in symbols or "ETH" in symbols


def test_928_missing_data_explicit():
    result = screener.run_asset_screener_928()
    for row in result["results"]:
        assert row.get("no_disguised_zero") is True


def test_928_pro_tier_save():
    denied = screener.save_screener_criteria_928("My Filter", {}, user_id="u1", tier="free")
    assert denied["error"] == "pro_tier_required"
    saved = screener.save_screener_criteria_928("My Filter", {}, user_id="u1", tier="pro")
    assert saved["saved"] is True


def test_928_export_via_924():
    export = screener.export_screener_via_export_layer_928(fmt="json")
    assert export["export_ref"] == 924
    assert export["export"]["ok"] is True


# --- #930 Bridges Intelligence ---


def test_930_bridge_flows_status(onchain_seed):
    status = onchain.bridge_flows_status_930(seed=onchain_seed)
    assert status["bridge_mapping_audited"] is True
    assert status["standalone_rejected"] is True


def test_930_bridge_aggregation(onchain_seed):
    dashboard = onchain.build_bridge_flows_dashboard_930(seed=onchain_seed)
    assert dashboard["ok"] is True
    assert dashboard["flow_count"] >= 1
    assert dashboard["rule_based_only"] is True


# --- #937 Cross-Chain Trace ---


def test_937_cross_chain_trace(onchain_seed):
    trace = onchain.trace_cross_chain_path_937("0xabc123def456", seed=onchain_seed)
    assert trace["ok"] is True
    assert trace["hop_count"] >= 2
    assert all("confidence" in h for h in trace["hops"])


def test_937_bridge_mappings_audited(onchain_seed):
    trace = onchain.trace_cross_chain_path_937("0xabc123def456", seed=onchain_seed)
    assert trace["bridge_mappings_audited"] is True


# --- #931 Verification Engine ---


def test_931_verification_status(verification_seed):
    status = verification.verification_engine_status_931(seed=verification_seed)
    assert status["standalone_rejected"] is True
    assert status["no_post_hoc_editing"] is True


def test_931_freeze_claim(verification_seed):
    frozen = verification.freeze_claim_931(
        asset="BTC",
        claim_text="Test",
        target_definition={"metric": "price_usd", "threshold": 60000, "direction": "above"},
        horizon_days=5,
        seed=verification_seed,
    )
    assert frozen["frozen"] is True
    assert frozen["claim"]["lock_hash"] is not None


def test_931_deterministic_grading(verification_seed):
    tests = verification.run_verification_grading_tests_931(seed=verification_seed)
    assert tests["all_passed"] is True


def test_931_no_post_hoc_edit(verification_seed):
    verification.resolve_claim_931("claim_001", seed=verification_seed)
    double = verification.resolve_claim_931("claim_001", seed=verification_seed)
    assert double.get("error") == "already_resolved"


def test_931_unresolved_stays(verification_seed):
    unresolved = verification.resolve_claim_931("claim_003", seed=verification_seed)
    assert unresolved.get("status") == "unresolved"


def test_931_verification_e2e(verification_seed):
    e2e = verification.run_verification_engine_e2e_931(seed=verification_seed)
    assert e2e["all_passed"] is True


# --- #938 Decision Intelligence ---


def test_938_decision_status(decision_seed):
    status = decision.decision_intelligence_status_938(seed=decision_seed)
    assert status["standalone_rejected"] is True
    assert status["no_action_claims"] is True


def test_938_evidence_normalization(decision_seed):
    evidence = decision.normalize_evidence_938(seed=decision_seed)
    assert evidence["domain_count"] >= 3


def test_938_contradiction_detection(decision_seed):
    contradictions = decision.detect_contradictions_938(seed=decision_seed)
    assert contradictions["count"] >= 1


def test_938_reasoning_chain(decision_seed):
    chain = decision.build_reasoning_chain_938("BTC", seed=decision_seed)
    assert chain["ok"] is True
    assert len(chain["reasoning_chain"]) == 6
    assert chain["no_unsupported_action_claim"] is True
    assert all(s.get("claim_type") for s in chain["reasoning_chain"])


def test_938_decision_e2e(decision_seed):
    e2e = decision.run_decision_intelligence_e2e_938(seed=decision_seed)
    assert e2e["all_passed"] is True


# --- On-Chain Extension E2E (includes #930/#937) ---


def test_onchain_extension_e2e_batch28(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True
