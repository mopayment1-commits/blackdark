"""Tests — Batch 31: #950 Stabilization, #951 DeFi Strategy Risk, #952 Decision Certificate, #953 Dev Activity, #955 Traceability."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_provenance_layer as prov
from bd_platform import data_engine_stabilization_metadata as stab
from bd_platform import intelligence_ledger_decision_certificate as cert
from bd_platform import portfolio_ai_defi_strategy_risk as defi_risk
from bd_platform import protocol_kpi_intelligence as kpi


@pytest.fixture
def stab_seed() -> dict:
    return json.loads(Path("data/data_engine_stabilization_metadata_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def cert_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_decision_certificate_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def defi_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_defi_strategy_risk_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def kpi_seed() -> dict:
    return json.loads(Path("data/protocol_kpi_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    stab.reset_stabilization_state()
    cert.reset_decision_certificate_state()
    yield
    stab.reset_stabilization_state()
    cert.reset_decision_certificate_state()


# --- #950 Data Stabilization ---


def test_950_status_merged_into_data_engine(stab_seed):
    status = stab.stabilization_status_950(seed=stab_seed)
    assert status["standalone_rejected"] is True
    assert status["revision_semantics_explicit"] is True
    assert status["stabilization_blocks"]["utxo"] == 6
    assert status["stabilization_blocks"]["account"] == 12


def test_950_fresh_provisional_stabilized_badges(stab_seed):
    fresh = stab.get_metric_stability_badge_950("sol_active_addresses", seed=stab_seed)
    assert fresh["status"] == "fresh"
    assert fresh["can_mutate"] is True

    prov_badge = stab.get_metric_stability_badge_950("btc_utxo_balance", seed=stab_seed)
    assert prov_badge["status"] == "provisional"
    assert prov_badge["can_mutate"] is True

    stabilized = stab.get_metric_stability_badge_950("eth_account_tvl", seed=stab_seed)
    assert stabilized["status"] == "stabilized"
    assert stabilized["can_mutate"] is False


def test_950_revision_and_cache_invalidation(stab_seed):
    rev = stab.log_metric_revision_950(
        "btc_utxo_balance",
        old_value=100,
        new_value=101,
        post_stabilization=True,
        seed=stab_seed,
    )
    assert rev["historical_correction_audited"] is True
    assert rev["revision"]["no_silent_update"] is True
    assert rev["cache_invalidation"]["cache_invalidation_tested"] is True

    hist = stab.get_revision_history_950("btc_utxo_balance", seed=stab_seed)
    assert hist["count"] >= 1
    assert hist["historical_corrections_audited"] is True


def test_950_e2e(stab_seed):
    e2e = stab.run_stabilization_e2e_950(seed=stab_seed)
    assert e2e["all_passed"] is True


# --- #951 DeFi Strategy Risk ---


def test_951_status_no_guaranteed_yield(defi_seed):
    status = defi_risk.defi_strategy_risk_status_951(seed=defi_seed)
    assert status["standalone_rejected"] is True
    assert status["no_guaranteed_yield"] is True
    assert status["historical_apy_only"] is True
    assert status["risk_insight_not_protection"] is True


def test_951_strategy_report_dependency_graph(defi_seed):
    report = defi_risk.build_strategy_risk_report_951("eth_loop_aave", seed=defi_seed)
    assert report["ok"] is True
    assert report["no_guaranteed_yield"] is True
    assert report["not_expected_return"] is True
    assert len(report["dependency_graph"]) >= 2
    assert "impermanent_loss" in report["scenarios"]


def test_951_il_liquidation_scenarios(defi_seed):
    lp = defi_risk.build_strategy_risk_report_951("uni_lp_eth_usdc", seed=defi_seed)
    assert lp["scenarios"]["impermanent_loss"] == "high"
    assert lp["risk_insight_not_protection"] is True


def test_951_e2e(defi_seed):
    e2e = defi_risk.run_defi_strategy_risk_e2e_951(seed=defi_seed)
    assert e2e["all_passed"] is True


# --- #952 Decision Certificate ---


def test_952_status_immutable_evidence(cert_seed):
    status = cert.decision_certificate_status_952(seed=cert_seed)
    assert status["standalone_rejected"] is True
    assert status["reproducible_export"] is True
    assert status["no_mutable_evidence"] is True
    assert status["verification_id_resolves_snapshot"] is True


def test_952_freeze_and_tenant_isolation(cert_seed):
    frozen = cert.freeze_decision_certificate_952(
        decision_summary="Test allocation",
        evidence=[{"source": "onchain", "metric": "tvl", "value": 1_000_000}],
        risk_score=42.5,
        confidence="medium",
        model_versions={"risk": "2.0.0"},
        tenant_id="tenant_alpha",
        seed=cert_seed,
    )
    cert_id = frozen["certificate"]["certificate_id"]
    assert frozen["frozen"] is True
    assert frozen["certificate"]["evidence_hash"] is not None
    assert frozen["certificate"]["verification_id"] == frozen["certificate"]["evidence_hash"][:16]

    allowed = cert.get_decision_certificate_952(cert_id, tenant_id="tenant_alpha", seed=cert_seed)
    assert allowed["ok"] is True

    denied = cert.get_decision_certificate_952(cert_id, tenant_id="tenant_other", seed=cert_seed)
    assert denied["error"] == "tenant_denied"


def test_952_reproducible_export(cert_seed):
    exp1 = cert.export_decision_certificate_952(
        "cert_aave_allocation_001",
        tenant_id="tenant_alpha",
        seed=cert_seed,
    )
    exp2 = cert.export_decision_certificate_952(
        "cert_aave_allocation_001",
        tenant_id="tenant_alpha",
        seed=cert_seed,
    )
    assert exp1["reproducible"] is True
    assert exp1["export_hash"] == exp2["export_hash"]
    assert exp1["evidence_manifest"]["verification_id"] is not None


def test_952_pdf_export(cert_seed):
    pdf = cert.export_decision_certificate_952(
        "cert_aave_allocation_001",
        fmt="pdf",
        tenant_id="tenant_alpha",
        seed=cert_seed,
    )
    assert pdf["format"] == "pdf"
    assert pdf["content"]["format"] == "pdf"


# --- #953 Development Activity ---


def test_953_status_methodology(kpi_seed):
    status = kpi.development_activity_status_953(seed=kpi_seed)
    assert status["repo_mapping_audited"] is True
    assert status["forks_noise_filtered"] is True
    assert status["merge_commits_excluded"] is True
    assert len(status["metrics"]) == 4


def test_953_repo_mapping_audit(kpi_seed):
    mapping = kpi.get_repo_mapping_audit_953("uniswap", seed=kpi_seed)
    assert mapping["ok"] is True
    assert mapping["repo_mapping_audited"] is True
    assert len(mapping["canonical_repos"]) >= 1
    assert len(mapping["forks_excluded"]) >= 1


def test_953_development_activity_chart(kpi_seed):
    chart = kpi.build_development_activity_chart_953("uniswap", seed=kpi_seed)
    assert chart["ok"] is True
    assert chart["fork_noise_filtered"] is True
    assert chart["methodology"]["merge_commits_excluded"] is True
    assert chart["metrics"]["commits_per_month"] is not None


# --- #955 Decision Traceability ---


def test_955_complete_trace(cert_seed):
    trace = cert.verify_decision_trace_955("trace_dec_aave_alloc_001", tenant_id="tenant_alpha", seed=cert_seed)
    assert trace["complete"] is True
    assert trace["verification_passed"] is True
    assert trace["broken_links"] == []
    assert trace["deterministic_replay"] is True


def test_955_broken_link_fails(cert_seed):
    broken = cert.verify_decision_trace_955("trace_broken_sample", tenant_id="tenant_alpha", seed=cert_seed)
    assert broken["ok"] is False
    assert broken["broken_link_fails_verification"] is True
    assert len(broken["broken_links"]) > 0


def test_955_tenant_isolation(cert_seed):
    denied = cert.verify_decision_trace_955("trace_dec_aave_alloc_001", tenant_id="tenant_other", seed=cert_seed)
    assert denied["error"] == "tenant_denied"


def test_955_audit_export(cert_seed):
    audit = cert.export_decision_trace_audit_955("trace_dec_aave_alloc_001", tenant_id="tenant_alpha", seed=cert_seed)
    assert audit["audit_export"]["complete"] is True
    assert audit["tenant_isolation"] is True


def test_955_provenance_integration():
    trace = prov.verify_decision_trace_integration_955("trace_dec_aave_alloc_001", tenant_id="tenant_alpha")
    assert trace["complete"] is True


def test_952_e2e(cert_seed):
    e2e = cert.run_decision_certificate_e2e_952(seed=cert_seed)
    assert e2e["all_passed"] is True


# --- Regression batch 30 provenance ---


def test_945_e2e_includes_955():
    e2e = prov.run_provenance_layer_e2e()
    assert e2e["all_passed"] is True
    assert 955 in e2e["feature_refs"]


def test_986_e2e_includes_953(kpi_seed):
    e2e = kpi.run_protocol_kpi_e2e(seed=kpi_seed)
    assert e2e["all_passed"] is True
    assert 953 in e2e["feature_refs"]
