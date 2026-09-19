"""Launch-57 Failure, Degraded Mode, Error & Recovery baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.failure_recovery_common import (
    INTERNAL_RECOVERY_COMPONENTS,
    FAILURE_RECOVERY_VERSION,
    acceptance_criteria_status,
    attach_failure_recovery_envelope,
    build_ai_failure_context,
    build_alert_delivery_failure_context,
    build_canonical_error_envelope,
    build_degradation_context,
    build_recovery_component_registry,
    build_reconciliation_context,
    map_freshness_to_runtime_state,
    record_degradation_signal,
)
from failure.states import FailureState


def test_internal_components_all_have_consumers():
    registry = build_recovery_component_registry()
    assert len(registry) == len(INTERNAL_RECOVERY_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"
        assert row["launch_surface"] is False
        assert row["standalone_capability"] is False
        assert row["consumer_capability_ids"]


def test_stale_maps_to_stale_runtime_state():
    assert map_freshness_to_runtime_state("STALE") == FailureState.STALE
    assert map_freshness_to_runtime_state("UNKNOWN") == FailureState.UNAVAILABLE


def test_degradation_context_abstain_on_conflict():
    ctx = build_degradation_context(
        freshness_state="LIVE",
        quality_state="insufficient",
        conflicting=True,
    )
    assert ctx["abstain_reachable"] is True
    assert ctx["runtime_state"] == FailureState.DEGRADED.value


def test_stale_cannot_appear_live():
    ctx = build_degradation_context(freshness_state="STALE", quality_state="decision_grade")
    assert ctx["stale_cannot_appear_live"] is True


def test_canonical_error_envelope_machine_readable():
    err = build_canonical_error_envelope(
        title="connector_unavailable",
        detail="no route",
        affected_capability=42,
    )
    assert err["error_code"]
    assert err["correlation_id"].startswith("bd-")
    assert "retryable" in err
    assert "certainty" in err


def test_ai_failure_preserves_evidence():
    ctx = build_ai_failure_context(evidence_intact=True, presentation_failed=True)
    assert ctx["preserve_non_ai_data"] is True
    assert ctx["runtime_state"] == FailureState.DEGRADED.value


def test_ai_failure_blocks_confident_analysis_without_evidence():
    ctx = build_ai_failure_context(evidence_intact=False)
    assert ctx["runtime_state"] == FailureState.UNAVAILABLE.value


def test_alert_delivery_does_not_mutate_decision():
    ctx = build_alert_delivery_failure_context(
        trigger_time="2026-09-18T12:00:00Z",
        generation_time="2026-09-18T12:00:01Z",
        delivery_state="BLOCKED",
        retry_scheduled=False,
    )
    assert ctx["decision_state_mutated"] is False
    assert ctx["retry_scheduled"] is False


def test_reconciliation_blocks_entitlement_grant():
    ctx = build_reconciliation_context()
    assert ctx["grant_entitlement_from_uncertain"] is False
    assert ctx["retry_policy"] == "RECONCILE_FIRST"


def test_attach_failure_recovery_envelope_on_error():
    body = {
        "launch_item_id": 42,
        "capability_id": 504,
        "success": False,
        "error": "no_exchange_route_available",
        "freshness_state": "UNKNOWN",
    }
    out = attach_failure_recovery_envelope(body, launch_item_id=42)
    assert out["launch57_failure_recovery"]["internal_support_only"] is True
    assert out["launch57_failure_recovery"]["canonical_error"] is not None
    assert out["launch57_failure_recovery"]["false_success_blocked"] is True


def test_attach_failure_recovery_envelope_success_path():
    body = {
        "launch_item_id": 22,
        "success": True,
        "freshness_state": "LIVE",
        "provenance": {"quality_state": "decision_grade"},
    }
    out = attach_failure_recovery_envelope(body, launch_item_id=22)
    degraded = out["launch57_failure_recovery"]["degradation_context"]
    assert degraded["runtime_state"] == FailureState.SUCCESS.value


def test_degradation_signal_persisted(tmp_path, monkeypatch):
    store = tmp_path / "launch57_failure_degradation_signals.jsonl"
    monkeypatch.setattr("launch57.failure_recovery_common._DEGRADATION_STORE", store)
    row = record_degradation_signal(
        capability_id=42,
        runtime_state="UNAVAILABLE",
        failure_class="MARKET_DATA",
        detail="connector test",
    )
    assert row["signal_id"].startswith("fdr_sig_")
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_acceptance_criteria_core_checks():
    status = acceptance_criteria_status()
    assert status["ac03_stale_cannot_appear_live"] is True
    assert status["ac05_abstain_reachable"] is True
    assert status["ac07_indeterminate_reconcile_before_retry"] is True
    assert status["ac21_no_false_pass_live"] is True


def test_stale_gate_body_includes_failure_recovery():
    from launch57.decision_common import stale_gate_body

    body = stale_gate_body(
        capability_id=2,
        launch_item_id=2,
        surface="oracle",
        symbol="BTC",
        spine={"freshness_state": "STALE", "data_spine": {}},
        entrypoint="test_entry",
    )
    assert "launch57_failure_recovery" in body
    assert body["success"] is False
    assert body["presented_as_live"] is False
