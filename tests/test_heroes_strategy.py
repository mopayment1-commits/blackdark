"""Binding Heroes Strategy + Section Z deepenings."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_audience_routing():
    from audience_routing import audience_entry, normalize_audience

    assert normalize_audience("fund") == "fund"
    retail = audience_entry("retail")
    assert retail["first_screen"] == "single_sentence_oracle"
    assert "single_sentence_oracle" in retail["heroes"]
    whale = audience_entry("whale")
    assert whale["first_screen"] == "stealth_execution_advisor"
    assert "#stealth" in whale["entry_path"]


def test_decision_certificate_and_compliance_footer():
    from decision_certificate import build_decision_certificate, compliance_footer_block

    cert = build_decision_certificate(
        {
            "symbol": "BTC",
            "prediction_id": 99,
            "chain_hash": "abc123",
            "decision_action": "ACT",
            "decision_sentence": "Clear opportunity on BTC",
            "opportunity_score": 72,
        }
    )
    assert cert["certificate_hash"]
    assert "BTC" in cert["share_text"]
    foot = compliance_footer_block(surface="oracle", trust_basis="ledger")
    assert "Not financial advice" in foot["disclaimer"]


def test_locked_predictions_seal_and_list(tmp_path, monkeypatch):
    import locked_predictions as lp

    monkeypatch.setattr(lp, "_PATH", tmp_path / "locked.jsonl")
    unlock = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    row = lp.lock_prediction(
        event_name="FOMC",
        asset="BTC",
        direction="bullish",
        rationale="Risk-on into cut",
        unlock_at=unlock,
        opportunity_score=70,
    )
    assert row["status"] == "locked"
    assert "direction" not in row
    listed = lp.list_locked_predictions(limit=5)
    assert listed[0]["seal_hash"]


def test_discipline_mirror_private(tmp_path, monkeypatch):
    import discipline_mirror as dm

    monkeypatch.setattr(dm, "_PATH", tmp_path / "mirror.jsonl")
    dm.record_follow_up(
        user_key="user@example.com",
        asset="ETH",
        system_action="ACT",
        followed=False,
        prediction_id=1,
    )
    mirror = dm.personal_mirror("user@example.com")
    assert mirror["private"] is True
    assert mirror["ignored_count"] == 1
    assert mirror["follow_rate_percent"] == 0.0


def test_whale_signal_vs_noise_classifier():
    from whale_signal_classifier import classify_whale_alert

    noise = classify_whale_alert(
        {"asset": "BTC", "direction": "in", "amount_usd": 5e7, "detail": "cold wallet custody transfer"}
    )
    assert noise["label"] == "NOISE"
    assert noise["actionable"] is False

    hedged = classify_whale_alert(
        {"asset": "BTC", "direction": "buy", "amount_usd": 2e7, "detail": "exchange inflow"},
        derivatives_context={"funding_rate": -0.0005},
    )
    assert hedged["class_id"] == "hedged_or_basis_trade"
    assert hedged["actionable"] is False


def test_constitution_gates_half_life_and_alertable():
    from constitution_gates import apply_half_life_kill, is_alertable

    row = {
        "execution_feasibility": "full",
        "opportunity_half_life": {"remaining_seconds": 1, "disappearance_probability": 0.95},
    }
    apply_half_life_kill(row)
    assert row["half_life_killed"] is True
    assert is_alertable(row) is False


def test_stealth_advisor_and_discipline_delta():
    from discipline_mirror import personal_mirror
    from stealth_execution_advisor import advise_stealth_execution

    tip = advise_stealth_execution(asset="BTC", notional_usd=2_000_000, half_life_seconds=12)
    assert tip["recommended_slices"] >= 1
    assert tip["status"] == "advisory_v2"
    assert tip.get("adv_source")

    mirror = personal_mirror(
        "u1",
        label_by_id={},
    )
    assert mirror["private"] is True
    assert "delta_plain_english" in mirror


def test_english_ui_includes_discipline_page():
    from pathlib import Path

    text = Path("templates/discipline.html").read_text(encoding="utf-8")
    assert "lang=" in text
    assert "Discipline Mirror" in text


def test_mev_sandwich_report_shareable():
    from mev_sandwich_report import build_mev_sandwich_report

    report = build_mev_sandwich_report(asset="ETH", notional_usd=25_000)
    assert report["estimated_sandwich_bps"] > 0
    assert "share_text" in report
    assert report["compliance"]["disclaimer"]


def test_glass_box_challenge_pack():
    from glass_box_challenge import build_glass_box_challenge_pack

    pack = build_glass_box_challenge_pack()
    assert pack["status"] == "ready_pack"
    assert "exact_datetime" in pack["launch_only_fields"]
    assert "Prove it" in pack["challenge_text_en"]
    assert pack["product_surfaces"]["public_accuracy_ledger"] == "/oracle-accuracy"


def test_alerts_generosity_and_inbox_stats():
    from in_app_alerts import inbox_stats

    stats = inbox_stats()
    assert "15-alerts" in stats["generosity_note"] or "TradingView" in stats["generosity_note"]


def test_report_inventory_covers_section_ten():
    from pathlib import Path

    text = Path("docs/REPORT_INVENTORY_STATUS.md").read_text(encoding="utf-8")
    assert "MEV/Sandwich" in text
    assert "Glass Box Challenge" in text
    assert "UNDER_STUDY" in text
    assert "Browser Extension" in text or "Browser extension" in text
    deferred = Path("docs/DEFERRED_HUMAN_STEPS.md").read_text(encoding="utf-8")
    assert "H1" in deferred and "H2" in deferred and "H3" in deferred


def test_heroes_http_endpoints():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    assert client.get("/api/mev/sandwich-report?asset=ETH&notional_usd=10000").status_code == 200
    assert client.get("/api/glass-box/challenge").status_code == 200
    assert client.get("/api/alerts/generosity").status_code == 200
    assert client.get("/api/compliance/footer?surface=oracle").status_code == 200
    assert client.get("/api/audit-challenge").status_code == 200
    assert client.get("/robots.txt").status_code == 200
    assert client.get("/sitemap.xml").status_code == 200
    stealth = client.post(
        "/api/whale/stealth-advisor",
        json={"asset": "ETH", "notional_usd": 100000, "side": "buy"},
    )
    assert stealth.status_code == 200
    assert stealth.json()["recommended_slices"] >= 1
