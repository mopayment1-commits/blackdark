"""Adaptive v4 security verification tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bd_platform.adaptive_intelligence.mirror_ledger import record_user_decision
from bd_platform.adaptive_intelligence.security_controls import threat_model_delta, validate_adaptive_input


def test_input_validation_rejects_injection():
    r = validate_adaptive_input({"query": "<script>alert(1)</script>"})
    assert not r["ok"]
    assert "query_invalid_chars" in r["errors"]


def test_input_validation_rejects_oversized():
    r = validate_adaptive_input({"query": "x" * 3000})
    assert not r["ok"]


def test_input_validation_accepts_clean():
    r = validate_adaptive_input({"query": "decide BTC", "intent_id": "decide"})
    assert r["ok"]


def test_mirror_ledger_consent_required():
    with pytest.raises(ValueError, match="mirror_ledger_requires_consent"):
        record_user_decision(user_id="u1", decision_ref="d1", user_stance="wait", consent=False)


def test_mirror_ledger_not_financial_ground_truth():
    row = record_user_decision(user_id="u1", decision_ref="d1", user_stance="wait", consent=True)
    assert row["financial_ground_truth"] is False


def test_threat_model_documents_new_boundaries():
    delta = threat_model_delta()
    assert "/api/adaptive/*" in delta["delta"]["new_api_entry_points"]
    assert delta["certification_claimed"] is False


def test_api_rejects_invalid_input():
    import dashboard

    client = TestClient(dashboard.app)
    r = client.post("/api/adaptive/route", json={"query": "<bad>"})
    assert r.status_code == 400


def test_api_valid_route_succeeds():
    import dashboard

    client = TestClient(dashboard.app)
    r = client.post("/api/adaptive/route", json={"intent_id": "decide"})
    assert r.status_code == 200
    assert r.json()["stance"] in {"NEUTRAL", "ABSTAIN"}


def test_input_validation_rejects_unicode_control_chars():
    r = validate_adaptive_input({"query": "decide\u200bBTC"})
    assert not r["ok"]
    assert "query_invalid_chars" in r["errors"]


def test_input_validation_rejects_type_confusion():
    r = validate_adaptive_input({"intent_id": 12345})
    assert not r["ok"]
    assert "intent_id_must_be_string" in r["errors"]


def test_input_validation_rejects_malformed_user_id():
    r = validate_adaptive_input({"user_id": "../../admin"})
    assert not r["ok"]
    assert "user_id_invalid" in r["errors"]


def test_graph_causes_edge_requires_contract():
    from bd_platform.adaptive_intelligence.capability_graph import validate_edge

    with pytest.raises(ValueError, match="causal_evidence_contract"):
        validate_edge({"source_id": "a", "target_id": "b", "edge_type": "CAUSES"})


def test_playbook_mutation_requires_validation_state():
    from bd_platform.adaptive_intelligence.playbook_governance import PlaybookContract

    contract = PlaybookContract(playbook_id="x", version="1", purpose="test", validation_state="bogus")
    with pytest.raises(ValueError, match="validation_state"):
        contract.validate_official()


def test_calibration_tampering_blocked():
    from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update({"symbol": "BTC", "numeric_confidence": 0.95})
    with pytest.raises(ValueError, match="numeric_confidence_requires_calibration_evidence"):
        build_adaptive_decision_contract(opp)


def test_human_validation_export_delete_supported():
    from bd_platform.adaptive_intelligence.human_validation import delete_sessions, export_sessions, infrastructure_status

    st = infrastructure_status()
    assert st["export_supported"] and st["delete_supported"]
    assert isinstance(export_sessions(), list)
    delete_sessions()


def test_role_preferences_no_escalation():
    from bd_platform.adaptive_intelligence.role_preferences import get_role_preferences

    r = get_role_preferences("institutional")
    assert r["restricts_capabilities"] is False
