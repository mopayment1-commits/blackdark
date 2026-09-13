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
