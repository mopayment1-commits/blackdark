"""Launch-57 TEIS (Temporal Evidence & Intelligence Support Layer) tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.teis_support_common import (
    INTERNAL_SUPPORT_COMPONENTS,
    acceptance_criteria_status,
    assess_replay_fidelity,
    attach_teis_support_envelope,
    build_evaluation_dependence_metadata,
    build_outcome_contract,
    build_reproducibility_manifest,
    build_teis_component_registry,
    check_temporal_leakage,
    map_internal_to_user_evidence,
    record_internal_failure_case,
)


def test_internal_components_all_have_consumers():
    registry = build_teis_component_registry()
    assert len(registry) == len(INTERNAL_SUPPORT_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"
        assert row["launch_surface"] is False
        assert row["standalone_capability"] is False
        assert row["consumer_capability_ids"]


def test_replay_and_shadow_never_map_to_live():
    assert map_internal_to_user_evidence("HISTORICAL_REPLAY") == "SIM"
    assert map_internal_to_user_evidence("SIMULATED") == "SIM"
    assert map_internal_to_user_evidence("FORWARD_SHADOW") == "SIM"


def test_stale_production_observed_downgrades_to_delayed():
    assert map_internal_to_user_evidence("PRODUCTION_OBSERVED", freshness_state="STALE") == "DELAYED"


def test_temporal_leakage_blocks_future_available_at():
    result = check_temporal_leakage("2026-09-18T14:00:00Z", "2026-09-18T12:00:00Z")
    assert result["leakage_detected"] is True
    assert result["ok"] is False


def test_temporal_leakage_allows_past_available_at():
    result = check_temporal_leakage("2026-09-18T10:00:00Z", "2026-09-18T12:00:00Z")
    assert result["leakage_detected"] is False
    assert result["ok"] is True


def test_outcome_contract_stays_unresolved():
    contract = build_outcome_contract(capability_id=2, evaluation_horizon="24h")
    assert contract["outcome_status"] == "UNRESOLVED"
    assert contract["realized_result"] is None
    assert contract["evaluator_independent"] is True


def test_replay_fidelity_low_not_promotable():
    result = assess_replay_fidelity(
        source_availability=False,
        timestamp_fidelity=True,
        schema_version_match=False,
        feature_availability=False,
    )
    assert result["fidelity_band"] == "LOW"
    assert result["promotable_to_high_confidence"] is False
    assert result["user_facing_evidence"] == "SIM"


def test_evaluation_dependence_warns_on_overlap():
    meta = build_evaluation_dependence_metadata(
        case_id="case-1",
        event_family="price_spike",
        dependence_cluster="market_data",
        raw_evaluation_count=1000,
    )
    assert meta["overlap_warning"] is True
    assert meta["effective_independent_sample_estimate"] == 1


def test_reproducibility_manifest_has_hash():
    manifest = build_reproducibility_manifest(capability_id=3)
    assert manifest["manifest_hash"]
    assert manifest["code_sha"]
    assert manifest["reproducible"] is True


def test_internal_failure_case_persisted(tmp_path, monkeypatch):
    store = tmp_path / "launch57_teis_failure_corpus.jsonl"
    monkeypatch.setattr("launch57.teis_support_common._FAILURE_STORE", store)
    row = record_internal_failure_case(
        capability_id=10,
        root_cause="source_conflict",
        case_type="conflicting_sources",
        remediation="add_regression_test",
    )
    assert row["launch_surface"] is False
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert persisted["case_id"] == row["case_id"]


def test_attach_teis_support_envelope_marks_internal_only():
    body = attach_teis_support_envelope({"source": "replay", "freshness_state": "LIVE"})
    teis = body["teis_support"]
    assert teis["internal_support_only"] is True
    assert teis["replay_is_not_live"] is True
    assert teis["user_facing_evidence"] == "SIM"
    assert teis["pass_engineering_not_granted_by_teis"] is True


def test_acceptance_criteria_all_true():
    status = acceptance_criteria_status()
    assert all(status.values())


@pytest.mark.asyncio
async def test_b4_decision_bridge_attaches_teis_envelope():
    from launch57.b4_decision_bridge import apply_b4_trust_envelope

    out = apply_b4_trust_envelope({"source": "oracle", "success": True})
    assert "teis_support" in out
    assert out["teis_support"]["internal_support_only"] is True
