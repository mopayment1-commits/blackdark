"""Trust OS expert-execution guardrails."""

from __future__ import annotations

from pathlib import Path


def test_trust_os_four_layers_and_denylist():
    from trust_os import OVERCLAIM_DENYLIST, VALUE_LAYERS, trust_os_manifest

    assert len(VALUE_LAYERS) == 4
    ids = {layer["id"] for layer in VALUE_LAYERS}
    assert ids == {
        "decision_intelligence",
        "transparency_evidence",
        "market_execution_edge",
        "institutional_packaging",
    }
    manifest = trust_os_manifest()
    assert "Verify" in manifest["thesis"]
    claims = " ".join(row["claim"] for row in OVERCLAIM_DENYLIST).upper()
    assert "SOR" in claims
    assert "IFRS" in claims
    assert "SOC" in claims


def test_oracle_scenarios_sum_near_100():
    from oracle_scenarios import build_oracle_scenarios

    payload = {
        "price": 100.0,
        "opportunity_score": 62,
        "confidence": 55,
        "decision_action": "ACT",
        "verdict": "BUY",
        "market_regime": "trend",
        "explanation": {"top_3_factors": [{"factor": "Momentum", "source": "test"}]},
    }
    out = build_oracle_scenarios(payload)
    scen = out["scenarios"]
    total = sum(scen[k]["probability_pct"] for k in ("bull", "base", "bear"))
    assert 99.0 <= total <= 101.0
    assert out["engine"] == "oracle_scenarios_v1"
    assert scen["bull"]["expected_range"]["high"] > 100


def test_glass_box_event_template():
    from glass_box_challenge import build_glass_box_challenge_pack

    pack = build_glass_box_challenge_pack()
    assert "event_template" in pack
    assert len(pack["event_template"]["steps"]) >= 4
    assert "Prove it" in pack["challenge_text_en"]


def test_risk_status_honest_scope():
    from risk_manager import risk_status

    status = risk_status()
    assert "honest_scope" in status
    assert "institutional VaR 99% desk" in " ".join(status["honest_scope"]["not_shipped"])


def test_docs_and_ui_wire_trust_os():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "TRUST_OS_VALUE_LAYERS.md").is_file()
    assert (root / "docs" / "LOAD_TEST_RUN_LOG.md").is_file()
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    i18n = (root / "i18n_service.py").read_text(encoding="utf-8")
    # Phrase may live in i18n catalog after localization wiring
    assert (
        "Don't trust us. Verify us." in landing
        or "Don't trust us. Verify us." in i18n
        or "seal.s3.body" in landing
    )
    assert ("Prove" in landing and "Operate" in landing) or ("nav.prove" in landing and "nav.operate" in landing)
    assert "lens=prove" in landing or "Open Proof" in landing or "nav.open_proof" in landing
    assert "Room for funds" in landing or "data-room" in landing or "lenses.room" in landing
    caps = (root / "templates" / "utility.html").read_text(encoding="utf-8")
    assert "four value layers" in caps.lower() or "Four value layers" in caps
    b2b = (root / "templates" / "b2b.html").read_text(encoding="utf-8")
    assert "Emerging Fund" in b2b
    dash = (root / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "Evidence drawer" in dash
    assert "scenarios" in dash
    assert "Prove → Operate → Desk → Room" in dash


def test_alerts_generosity_honesty():
    from pathlib import Path

    heroes = (Path(__file__).resolve().parents[1] / "api" / "routers" / "heroes.py").read_text(
        encoding="utf-8"
    )
    assert "honest_policy" in heroes
    assert "infinite infra SLA" in heroes or "not an infinite" in heroes.lower()
