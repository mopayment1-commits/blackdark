"""Tests — Natural Language Interpreter #573."""

from __future__ import annotations

import json

import pytest

from bd_platform import natural_language_interpreter as nli


@pytest.fixture
def nli_seed(tmp_path, monkeypatch):
    p = tmp_path / "natural_language_interpreter_seed.json"
    p.write_text(json.dumps({
        "permissions": {
            "guest": ["market_conditions", "onchain_metrics", "news_panel"],
            "authenticated": ["exchange_flow", "portfolio_tracker"],
        },
        "fallback_messages": {
            "empty_query": "Please enter a question.",
            "ambiguous_query": "Please clarify.",
            "advisory_blocked": "Data only.",
        },
    }), encoding="utf-8")
    monkeypatch.setattr(nli, "_SEED_PATH", p)
    return p


def test_status_feature_573(nli_seed):
    status = nli.natural_language_interpreter_status()
    assert status["feature_id"] == 573
    assert status["acceptance_criteria"]["deterministic_tool_schemas"] is True
    assert status["acceptance_criteria"]["no_advisory_answers"] is True


def test_deterministic_tool_schemas(nli_seed):
    schemas = nli.build_tool_schemas()
    assert schemas["deterministic"] is True
    assert schemas["no_unsupported_execution"] is True
    assert "exchange_flow" in schemas["tools"]


def test_advisory_query_blocked(nli_seed):
    result = nli.interpret_query("Should I buy Bitcoin?")
    assert result["intent_type"] == "advisory_blocked"
    assert result["advisory_query_blocked"] is True
    assert result["no_advisory_answer"] is True
    assert "redirect_message" in result


def test_analytical_routing_exchange_flow(nli_seed):
    result = nli.interpret_query("What is Bitcoin exchange flow?", user_tier="authenticated")
    assert result["intent_type"] == "analytical"
    assert result["tool_id"] == "exchange_flow"
    assert result["deterministic_routing"] is True


def test_ambiguous_fallback(nli_seed):
    result = nli.interpret_query("hello there")
    assert result["safe_fallback"] is True
    assert result["intent_type"] == "ambiguous_query"


def test_empty_query_fallback(nli_seed):
    result = nli.interpret_query("")
    assert result["safe_fallback"] is True
    assert result["intent_type"] == "empty_query"


def test_permission_denied_guest_portfolio(nli_seed):
    result = nli.interpret_query("Show my portfolio exposure", user_tier="guest")
    assert result["permission_denied"] is True
    assert result["intent_type"] == "permission_denied"


def test_permission_check_helper(nli_seed):
    perm = nli.check_permission("portfolio_tracker", user_tier="guest")
    assert perm["permission_check"] is True
    assert perm["allowed"] is False


def test_reconciliation_tests(nli_seed):
    tests = nli.run_reconciliation_tests()
    assert tests["all_passed"] is True
    assert tests["test_count"] >= 5


def test_build_nli_panel_wraps_evidence(nli_seed):
    panel = nli.build_nli_panel("Show market conditions", user_tier="guest")
    assert panel.get("evidence_metadata") or panel.get("institutional_evidence")


def test_api_routes(nli_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/ask").status_code == 200
    assert "Natural Language Interpreter" in c.get("/ask").text
    assert c.get("/api/platform/intelligence-ledger/ux-layer/natural-language/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/ux-layer/natural-language/schemas").status_code == 200
    r = c.get(
        "/api/platform/intelligence-ledger/ux-layer/natural-language",
        params={"query": "Show market conditions", "user_tier": "guest"},
    )
    assert r.status_code == 200
    assert r.json().get("intent_type") == "analytical"
    adv = c.get(
        "/api/platform/intelligence-ledger/ux-layer/natural-language",
        params={"query": "Should I buy Bitcoin?"},
    )
    assert adv.json().get("advisory_query_blocked") is True
