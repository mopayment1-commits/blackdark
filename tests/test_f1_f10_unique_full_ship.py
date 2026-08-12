"""F1–F10 unique competitor-gap features — full ship gates."""

from __future__ import annotations

import asyncio
from pathlib import Path


def test_f1_miss_feed_and_f2_emotion_tax_still_live():
    from emotion_tax_receipt import build_emotion_tax_receipt
    from public_miss_feed import build_public_miss_feed

    feed = asyncio.run(build_public_miss_feed(limit=5))
    assert feed.get("page") == "/miss-feed"
    tax = build_emotion_tax_receipt(user_key="f2_test", overrides=2, notional_usd=1000)
    assert tax["estimated_emotion_tax_usd"] > 0
    assert tax["page"] == "/emotion-tax"


def test_f3_allocator_receipt_seal_and_pdf():
    from allocator_decision_receipt import (
        build_allocator_decision_receipt,
        render_allocator_receipt_pdf,
    )

    receipt = asyncio.run(build_allocator_decision_receipt(limit=5, fund_name="Test LP Fund"))
    assert receipt["feature_id"] == "F3"
    assert receipt["product_complete"] is False
    assert receipt["seal_hash"]
    pdf = render_allocator_receipt_pdf(receipt)
    assert pdf.startswith(b"%PDF")


def test_f4_transfer_intent_probabilities():
    from transfer_intent_probability import compute_transfer_intent

    row = compute_transfer_intent(
        asset="BTC",
        amount_usd=12_000_000,
        from_label="coinbase",
        to_label="cold",
    )
    probs = row["probabilities"]
    total = probs["custody_percent"] + probs["collateral_percent"] + probs["directional_percent"]
    assert abs(total - 100.0) < 0.2
    assert row["dominant_intent"] == "custody"
    assert "Transfers ≠ Trades" in row["doctrine"] or "Transfers" in row["share_text"]


def test_f5_silence_index():
    from industry_silence_index import build_industry_silence_index, register_event

    register_event(
        event_name="Test macro print",
        event_at="2026-08-01T00:00:00+00:00",
        peer_seals={"nansen": False, "arkham": False},
    )
    board = build_industry_silence_index()
    assert board["feature_id"] == "F5"
    assert board["silence_score"] >= 0
    assert board["events_scored"] >= 1


def test_f6_alert_passport_refused_vs_sent():
    from proof_gated_alert_passport import build_alert_passport, evaluate_alert_gate

    evaluate_alert_gate(user_key="f6_user", net_edge_pass=False)
    evaluate_alert_gate(user_key="f6_user", net_edge_pass=True, veto_clear=True, freshness_ok=True)
    passport = build_alert_passport(user_key="f6_user")
    assert passport["feature_id"] == "F6"
    assert passport["refused"] >= 1
    assert passport["sent"] >= 1
    assert "refused" in passport["headline"].lower() or "sent" in passport["headline"].lower()


def test_f7_visibility_cost_meter():
    from whale_visibility_cost import build_visibility_cost_meter

    meter = build_visibility_cost_meter(asset="ETH", notional_usd=250_000)
    assert meter["feature_id"] == "F7"
    assert meter["estimated_visibility_cost_usd"] > 0
    assert meter["total_visibility_bps"] > 0


def test_f8_validity_decay_map():
    from decision_validity_decay import build_validity_decay_map

    board = asyncio.run(build_validity_decay_map(limit=10))
    assert board["feature_id"] == "F8"
    assert board["sample_n"] >= 1
    assert board["decay_curve"]
    assert board["median_validity_minutes"] >= 0


def test_f9_sealed_desk_duel_flow():
    from sealed_desk_duel import accept_duel, create_duel, reveal_duel

    duel = create_duel(host_desk="Alpha", host_verdict="WAIT", invitee_desk="Beta")
    assert duel["host"]["commitment"]
    assert duel["host"]["verdict"] is None  # sealed until reveal
    accepted = accept_duel(duel["duel_id"], desk="Beta", verdict="ACT")
    assert accepted["status"] == "sealed"
    revealed = reveal_duel(duel["duel_id"], force=True)
    assert revealed["status"] == "revealed"
    assert revealed["result"]["agree"] is False


def test_f10_trust_debt_score():
    from trust_debt_score import build_trust_debt_score, record_trust_event

    record_trust_event(user_key="f10_user", kind="unverified_ai", weight=4)
    record_trust_event(user_key="f10_user", kind="ledger_decision", weight=3)
    score = build_trust_debt_score(user_key="f10_user")
    assert score["feature_id"] == "F10"
    assert 0 <= score["trust_debt_score"] <= 100


def test_f1_f10_closure_all_done():
    from f1_f10_unique_closure import build_f1_f10_unique_closure

    closure = asyncio.run(build_f1_f10_unique_closure())
    assert closure["design_complete"] is True
    assert closure["implementation_complete"] is True
    assert closure["product_complete"] is False
    assert closure["all_done"] is True
    assert closure["closed_count"] == 10
    assert closure["strict_confirmation"]["percent_complete"] == 100


def test_pages_and_modules_exist():
    modules = [
        "public_miss_feed.py",
        "emotion_tax_receipt.py",
        "allocator_decision_receipt.py",
        "transfer_intent_probability.py",
        "industry_silence_index.py",
        "proof_gated_alert_passport.py",
        "whale_visibility_cost.py",
        "decision_validity_decay.py",
        "sealed_desk_duel.py",
        "trust_debt_score.py",
        "f1_f10_unique_closure.py",
    ]
    for m in modules:
        assert Path(m).exists(), m
    templates = [
        "miss_feed.html",
        "emotion_tax.html",
        "allocator_receipt.html",
        "transfer_intent.html",
        "silence_index.html",
        "alert_passport.html",
        "visibility_cost.html",
        "validity_decay.html",
        "desk_duel.html",
        "trust_debt.html",
        "unique_ten.html",
    ]
    for t in templates:
        assert Path("templates", t).exists(), t
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    for route in [
        "/allocator-receipt",
        "/transfer-intent",
        "/silence-index",
        "/alert-passport",
        "/visibility-cost",
        "/validity-decay",
        "/desk-duel",
        "/trust-debt",
        "/unique-ten",
    ]:
        assert route in dash
    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    assert "/api/public/f1-f10-closure" in heroes
    assert Path("docs/F1_F10_UNIQUE_FULL_SHIP_AR.md").exists()


def test_http_f1_f10_endpoints():
    import os

    os.environ.setdefault("SOFT_LAUNCH", "true")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    r = client.get("/api/public/f1-f10-closure")
    assert r.status_code == 200
    body = r.json()
    assert body["all_done"] is True
    assert body["strict_confirmation"]["percent_complete"] == 100

    for path in [
        "/unique-ten",
        "/allocator-receipt",
        "/transfer-intent",
        "/silence-index",
        "/alert-passport",
        "/visibility-cost",
        "/validity-decay",
        "/desk-duel",
        "/trust-debt",
        "/miss-feed",
        "/emotion-tax",
    ]:
        assert client.get(path).status_code == 200, path

    assert client.get("/api/visibility-cost?asset=ETH&notional_usd=100000").status_code == 200
    assert client.get("/api/alert-passport?user_key=http_test").status_code == 200
    assert client.get("/api/trust-debt?user_key=http_test").status_code == 200
