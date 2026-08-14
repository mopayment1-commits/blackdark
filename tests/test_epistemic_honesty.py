"""Epistemic honesty + Changed-Mind Record — no theatrical WAIT."""

from __future__ import annotations

from pathlib import Path


def test_i_dont_know_is_a_public_verdict_not_neutral():
    from regulatory_compliance_guard import (
        PUBLIC_VERDICT_UNKNOWN,
        apply_regulatory_compliance,
        classify_internal_verdict,
        to_public_verdict,
    )

    assert to_public_verdict("I_DONT_KNOW") == PUBLIC_VERDICT_UNKNOWN
    assert classify_internal_verdict("I DON'T KNOW") == "unknown"
    assert classify_internal_verdict("WAIT") == "neutral"
    out = apply_regulatory_compliance(
        {
            "verdict": "BUY",
            "dimension_conflict": {"veto": True, "abstain": True, "severity": "severe"},
        }
    )
    assert out["verdict"] == PUBLIC_VERDICT_UNKNOWN
    assert out["i_dont_know"] is True
    assert "dimension_conflict_veto" in out["epistemic_reasons"]
    assert out["decision_action"] == PUBLIC_VERDICT_UNKNOWN


def test_insufficient_confidence_forces_i_dont_know():
    from confidence_truth import claim_insufficient
    from epistemic_honesty import apply_epistemic_honesty
    from regulatory_compliance_guard import PUBLIC_VERDICT_UNKNOWN

    payload = {"verdict": "BUY", "confidence_claim": claim_insufficient(label="oracle").to_dict()}
    out = apply_epistemic_honesty(payload)
    assert out["verdict"] == PUBLIC_VERDICT_UNKNOWN
    assert out["i_dont_know"] is True
    formed = apply_epistemic_honesty({"verdict": "BUY", "dimension_conflict": {"veto": False}})
    assert formed["i_dont_know"] is False
    assert formed["verdict"] == "BUY"


def test_unified_conflict_verdict_is_i_dont_know():
    from oracle_unified import unified_verdict_with_conflict
    from regulatory_compliance_guard import PUBLIC_VERDICT_UNKNOWN

    assert unified_verdict_with_conflict(80, "BTC", {"veto": True}) == PUBLIC_VERDICT_UNKNOWN
    assert unified_verdict_with_conflict(80, "BTC", {"abstain": True}) == PUBLIC_VERDICT_UNKNOWN


def test_persona_i_dont_know_on_veto_wait_on_net_edge_reject():
    from persona_clarity import build_persona_clarity

    veto = build_persona_clarity(
        asset="ETH",
        score=70,
        verdict="BUY",
        payload={"dimension_conflict": {"veto": True, "abstain": True}},
    )
    assert veto["action"] == "I_DONT_KNOW"
    assert "I DON'T KNOW" in veto["personas"]["retail"]["en"]

    reject = build_persona_clarity(
        asset="ETH",
        score=70,
        verdict="Do Not Touch",
        payload={"net_edge_truth": {"reject": True, "truth_score": 20}, "dimension_conflict": {"veto": False}},
    )
    assert reject["action"] == "WAIT"


def test_idk_accuracy_is_abstain_not_a_directional_hit():
    from ml.labeling_pipeline import score_verdict_accuracy

    outcome, score, direction = score_verdict_accuracy("I_DONT_KNOW", 100.0, 110.0)
    assert outcome == "abstain"
    assert score == 0.0
    assert direction == "flat"


def test_changed_mind_record_from_chain(tmp_path, monkeypatch):
    import oracle_audit_chain as chain
    from changed_mind_record import build_changed_mind_record

    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    chain.append_prediction_record(
        {
            "event": "prediction_created",
            "prediction_id": 1,
            "asset": "BTC",
            "verdict": "BULLISH_ANALYTICS",
            "source": "oracle",
        }
    )
    chain.append_prediction_record(
        {
            "event": "prediction_created",
            "prediction_id": 2,
            "asset": "BTC",
            "verdict": "I_DONT_KNOW",
            "source": "oracle",
        }
    )
    feed = build_changed_mind_record(limit=10)
    assert feed["surface"] == "public_changed_mind_record"
    assert feed["page"] == "/changed-mind"
    assert feed["count"] == 1
    row = feed["items"][0]
    assert row["from_bucket"] == "bullish"
    assert row["to_bucket"] == "unknown"
    assert row["to_verdict"] == "I_DONT_KNOW"


def test_decision_certificate_stamps_epistemic_fields():
    from decision_certificate import build_decision_certificate

    cert = build_decision_certificate(
        {
            "symbol": "BTC",
            "verdict": "I_DONT_KNOW",
            "decision_action": "I_DONT_KNOW",
            "i_dont_know": True,
            "epistemic_state": "i_dont_know",
            "epistemic_reasons": ["dimension_conflict_veto"],
            "opportunity_score": 48,
        }
    )
    assert cert["i_dont_know"] is True
    assert cert["public_verdict"] == "I_DONT_KNOW"
    assert "dimension_conflict_veto" in cert["epistemic_reasons"]


def test_changed_mind_page_and_api_exist():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app, follow_redirects=False)
    page = client.get("/changed-mind")
    assert page.status_code == 200
    assert "Changed-Mind" in page.text
    api = client.get("/api/public/changed-mind")
    assert api.status_code == 200
    body = api.json()
    assert body["surface"] == "public_changed_mind_record"
    assert body.get("product_complete") is False
    assert body.get("LIVE-MONEY-READY") in {None, False}
