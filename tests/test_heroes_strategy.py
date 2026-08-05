"""Binding Heroes Strategy + Section Z deepenings."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_audience_routing():
    from audience_routing import audience_entry, normalize_audience

    assert normalize_audience("fund") == "fund"
    retail = audience_entry("retail")
    assert retail["first_screen"] == "single_sentence_oracle"
    assert "single_sentence_oracle" in retail["heroes"]


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
    assert tip["status"] == "advisory_shell_v1"

    mirror = personal_mirror(
        "u1",
        label_by_id={},
    )
    assert mirror["private"] is True
    assert "delta_plain_english" in mirror


def test_english_ui_includes_discipline_page():
    from pathlib import Path

    text = Path("templates/discipline.html").read_text(encoding="utf-8")
    assert 'lang="en"' in text
    assert "Discipline Mirror" in text
