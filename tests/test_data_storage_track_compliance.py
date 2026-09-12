"""Tests for data/storage/track governance compliance — v4_v2 DSR."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data_governance.audit import assess_compliance, run_compliance_audit
from blackdark.data_governance.contracts import (
    CANONICAL_CONTRACTS,
    ensure_contracts_materialized,
    get_contract,
    list_contracts,
    validate_contract,
)
from blackdark.data_governance.evidence_integrity import append_integrity_manifest, verify_manifest_chain
from blackdark.data_governance.intelligence_receipt import issue_intelligence_receipt, verify_receipt
from blackdark.data_governance.lineage import inherit_evidence_origin, propagate_lineage
from blackdark.data_governance.pit_evidence import create_pit_contract, validate_pit_framing
from blackdark.data_governance.quality import evaluate_dataset_quality
from blackdark.data_governance.restore import run_restore_drill
from blackdark.data_governance.rights import check_rights
from cap646.evidence_class import assert_promotion_allowed


def test_canonical_contracts_materialized():
    ensure_contracts_materialized()
    contracts = list_contracts()
    assert len(contracts) >= 6
    for c in contracts:
        ok, missing = validate_contract(c)
        assert ok, f"contract {c['asset_id']} missing {missing}"


def test_rights_enforcement_blocks_do_not_use():
    allowed, reason = check_rights("rp_do_not_use", "storage")
    assert allowed is False
    assert "rights_denied" in reason


def test_rights_allows_proprietary_storage():
    allowed, _ = check_rights("rp_proprietary_internal", "storage")
    assert allowed is True


def test_evidence_origin_no_upgrade_via_transform():
    child = propagate_lineage(
        {"evidence_class": "SIMULATED", "signal_id": "sig_1"},
        {"evidence_class": "PRODUCTION_VERIFIED"},
        transform="aggregate",
    )
    assert child.get("evidence_class") != "PRODUCTION_VERIFIED" or "promotion_blocked" in child


def test_assert_promotion_denied_simulated_to_production():
    with pytest.raises(ValueError, match="evidence_promotion_denied"):
        assert_promotion_allowed("SIMULATED", "PRODUCTION_VERIFIED")


def test_pit_framing_rejects_fake_live_claim():
    ok, reason = validate_pit_framing(is_replay=True, claim_text="real-time prediction at event time")
    assert ok is False
    assert reason == "replay_labeled_as_live_prediction"


def test_pit_framing_accepts_correct_replay_language():
    ok, _ = validate_pit_framing(
        is_replay=True,
        claim_text="Current engine successfully detected the historical event under point-in-time replay",
    )
    assert ok is True


def test_intelligence_receipt_verifiable():
    receipt = issue_intelligence_receipt(
        artifact_type="decision",
        artifact_id="dec_test",
        source_snapshot_hash="abc123",
        evidence_class="SHADOW_LIVE_FORWARD",
        output={"action": "WAIT"},
    )
    ok, msg = verify_receipt(receipt)
    assert ok, msg


def test_quality_missing_not_silent_live():
    q = evaluate_dataset_quality(count=0, dataset="ohlcv")
    assert q["degraded"] is True
    assert q["confidence"] == 0.0
    assert q["data_state"] == "MISSING"


def test_restore_drill_integrity(tmp_path, monkeypatch):
    src = tmp_path / "data"
    src.mkdir()
    ledger = src / "decision_ledger.jsonl"
    ledger.write_text('{"decision_id":"d1"}\n', encoding="utf-8")
    # Point restore module at tmp
    from blackdark.data_governance import restore as restore_mod

    result = restore_mod.run_restore_drill(root=tmp_path)
    assert result["all_integrity_ok"] is True
    assert result["rto_met"] is True


def test_evidence_manifest_chain():
    append_integrity_manifest(producer="test", artifact_path="data/signal_registry.jsonl")
    result = verify_manifest_chain()
    assert result["valid"] is True
    assert result["records"] >= 1


def test_pit_contract_created():
    contract = create_pit_contract(
        replay_id="replay_test_1",
        knowledge_cutoff="2026-01-01T00:00:00+00:00",
        data_snapshot_hash="deadbeef",
        code_sha="cafebabe",
    )
    assert contract["integrity_label"] == "point-in-time-faithful"
    assert "pit_" in contract["pit_id"]


def test_compliance_audit_engineering_pass():
    result = assess_compliance()
    assert result["gate"]["engineering_pass"] is True
    assert result["contracts"]["all_valid"] is True
    assert result["prelaunch_core"]["signal_registry"] is True
    assert result["prelaunch_core"]["decision_ledger"] is True


def test_requirements_register_exists_after_audit():
    from scripts.data_storage_track_compliance_audit import build_requirements_register

    reqs = build_requirements_register()
    mandatory = [r for r in reqs if r["mandatory"] == "YES"]
    assert len(mandatory) >= 80
    assert any(r["req_id"] == "REQ-DSR-001" for r in reqs)
    assert any(r["req_id"] == "REQ-DSR-024" for r in reqs)


def test_oracle_chain_valid():
    from oracle_audit_chain import verify_chain

    result = verify_chain()
    assert result["valid"] is True


def test_asset_graph_coverage():
    from blackdark.data_governance.asset_graph import graph_stats, trace_artifact

    stats = graph_stats()
    assert stats["coverage_pct"] >= 85.0
    trace = trace_artifact(artifact_type="decision", artifact_id="dec_test")
    assert "graph_chain" in trace


def test_cost_guards_complete():
    from blackdark.data_governance.cost_guard import ensure_cost_guards, validate_cost_guard

    reg = ensure_cost_guards()
    assert len(reg.get("guards", {})) >= 6
    for aid in reg["guards"]:
        ok, missing = validate_cost_guard(aid)
        assert ok, missing
