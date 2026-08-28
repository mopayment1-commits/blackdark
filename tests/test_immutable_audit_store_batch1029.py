"""Tests — Immutable Recommendation Audit Store (#1029)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform.infrastructure_immutable_audit_store import (
    ImmutableAuditError,
    attach_immutable_audit,
    build_merkle_root,
    check_infrastructure_gate_1029,
    extract_evidence_from_recommendation,
    get_immutable_audit_trail,
    get_immutable_record,
    hash_datum,
    immutable_audit_status_1029,
    is_enforcement_enabled,
    lock_recommendation_evidence,
    reset_immutable_audit_state,
    run_daily_integrity_check,
    run_immutable_audit_e2e_1029,
    verify_record,
    attempt_delete_record,
    attempt_modify_record,
)


@pytest.fixture
def ias_seed() -> dict:
    return json.loads(Path("data/immutable_audit_store_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    reset_immutable_audit_state()
    yield
    reset_immutable_audit_state()


def test_1029_status_no_standalone(ias_seed):
    status = immutable_audit_status_1029(seed=ias_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["worm_physical"] is True
    assert status["policy"]["enforcement_enabled"] is False


def test_enforcement_disabled_by_default(ias_seed):
    assert is_enforcement_enabled(seed=ias_seed) is False


def test_hash_datum_deterministic():
    h1 = hash_datum({"price": 42000})
    h2 = hash_datum({"price": 42000})
    assert h1 == h2
    assert len(h1) == 64


def test_merkle_root():
    leaves = [hash_datum({"a": 1}), hash_datum({"b": 2})]
    root = build_merkle_root(leaves)
    assert len(root) == 64
    assert root == build_merkle_root(leaves)


def test_lock_recommendation_evidence(ias_seed):
    rec = {"headline": "Use cex_spot", "asset": "ETH"}
    evidence = [
        {
            "source": "binance",
            "content": {"price_usd": 3000},
            "transformation": "ingest",
            "version": "1.0.0",
            "confidence": "High",
        }
    ]
    locked = lock_recommendation_evidence(
        trace_id="trace_001",
        recommendation=rec,
        evidence_datums=evidence,
        seed=ias_seed,
    )
    assert locked["locked"] is True
    assert locked["worm"] is True
    assert locked["merkle_root"]
    assert locked["certificate_hash"]
    assert locked["fee_db"]["fee_db_logged"] is True


def test_verify_record(ias_seed):
    locked = lock_recommendation_evidence(
        trace_id="trace_002",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    result = verify_record(locked["verification_id"], seed=ias_seed)
    assert result["verified"] is True
    assert result["deterministic_replay"] is True


def test_worm_no_edit(ias_seed):
    locked = lock_recommendation_evidence(
        trace_id="trace_003",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    with pytest.raises(ImmutableAuditError):
        attempt_modify_record(locked["verification_id"], changes={"headline": "hacked"})


def test_worm_no_delete(ias_seed):
    locked = lock_recommendation_evidence(
        trace_id="trace_004",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    with pytest.raises(ImmutableAuditError):
        attempt_delete_record(locked["verification_id"])


def test_read_only_get_record(ias_seed):
    locked = lock_recommendation_evidence(
        trace_id="trace_005",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    result = get_immutable_record(locked["verification_id"])
    assert result["ok"] is True
    assert result["read_only"] is True


def test_extract_evidence_selective_scope():
    rec = {
        "recommended_route": {"source": "1inch", "price_usd": 3000},
        "routes": [{"source": "binance", "price_usd": 2999}],
        "slippage_optimization": {"optimal_slippage_bps": 50},
    }
    evidence = extract_evidence_from_recommendation(rec)
    assert len(evidence) >= 3
    sources = {e["source"] for e in evidence}
    assert "1inch" in sources or "binance" in sources


def test_attach_immutable_audit_enforcement_off(ias_seed):
    rec = {"headline": "test", "recommended_route": {"source": "binance"}}
    out = attach_immutable_audit(rec, trace_id="trace_006", seed=ias_seed)
    assert out["immutable_audit"]["enforcement_enabled"] is False
    assert out["immutable_audit"]["infrastructure_ready"] is True


def test_attach_immutable_audit_enforcement_on(ias_seed):
    seed = json.loads(json.dumps(ias_seed))
    seed["immutable_recommendation_audit_store_1029"]["policy"]["enforcement_enabled"] = True
    rec = {
        "headline": "Use 1inch",
        "recommended_route": {"source": "1inch", "price_usd": 3000},
        "routes": [{"source": "binance", "price_usd": 2999}],
    }
    out = attach_immutable_audit(rec, trace_id="trace_007", seed=seed)
    assert out["immutable_audit"]["locked"] is True
    assert out.get("trace_id") == "trace_007"


def test_daily_integrity_check(ias_seed):
    lock_recommendation_evidence(
        trace_id="trace_008",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    result = run_daily_integrity_check(seed=ias_seed)
    assert result["mismatches"] == 0
    assert result["records_checked"] >= 1


def test_infrastructure_gate(ias_seed):
    gate = check_infrastructure_gate_1029(seed=ias_seed)
    assert gate["infrastructure_ready"] is True
    assert gate["blocks_production"] is True


def test_audit_trail(ias_seed):
    lock_recommendation_evidence(
        trace_id="trace_009",
        recommendation={"headline": "test"},
        evidence_datums=[{"source": "test", "content": {"x": 1}, "transformation": "t", "version": "1", "confidence": "High"}],
        seed=ias_seed,
    )
    trail = get_immutable_audit_trail()
    assert trail["count"] >= 1
    assert trail["read_only"] is True


def test_e2e_all_checks(ias_seed):
    e2e = run_immutable_audit_e2e_1029(seed=ias_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
