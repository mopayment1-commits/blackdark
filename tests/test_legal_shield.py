"""Strict Disclaimer Architecture (4-layer) tests."""

from __future__ import annotations

from pathlib import Path

from legal_shield import (
    CONSENT_ACK_TEXT,
    IS_FINANCIAL_ADVISOR,
    MANDATORY_DISCLAIMER_PREFIX,
    PERMANENT_FOOTER_TEXT,
    REGULATORY_STATUS,
    SYSTEM_CLASSIFICATION,
    apply_legal_shield,
    prefix_disclaimer,
    system_classification_payload,
)


def test_layer1_mandatory_prefix_hardcoded():
    out = prefix_disclaimer("BTC wait — score 42")
    assert out.startswith("DISCLAIMER:")
    assert "not financial advice" in out.lower()
    assert "BTC wait" in out
    # Idempotent
    assert prefix_disclaimer(out) == out


def test_layer1_apply_on_oracle_payload():
    payload = apply_legal_shield(
        {
            "verdict": "WAIT",
            "oracle": "Neutral observe on BTC",
            "decision_sentence": "WAIT on BTC",
            "action": "WAIT",
        }
    )
    assert payload["oracle"].startswith(MANDATORY_DISCLAIMER_PREFIX[:20])
    assert payload["action"] == "WAIT"  # short label not prefixed
    assert payload["is_investment_advice"] is False
    assert payload["is_financial_advisor"] is False


def test_layer2_classification_constants():
    assert SYSTEM_CLASSIFICATION == "analytical_tool"
    assert IS_FINANCIAL_ADVISOR is False
    assert REGULATORY_STATUS == "not_regulated"
    meta = system_classification_payload()
    assert meta["system_classification"] == "analytical_tool"
    assert meta["is_financial_advisor"] is False
    assert len(meta["legal_shield_layers"]) == 4


def test_layer3_consent_ack_text():
    assert "not a financial advisor" in CONSENT_ACK_TEXT.lower()
    assert "full responsibility" in CONSENT_ACK_TEXT.lower()


def test_layer4_permanent_footer_text():
    assert "analytical tool" in PERMANENT_FOOTER_TEXT.lower()
    assert "not financial advice" in PERMANENT_FOOTER_TEXT.lower()


def test_frontend_shield_assets_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "static" / "js" / "legal-shield.js").is_file()
    assert (root / "static" / "css" / "legal-shield.css").is_file()
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    assert "legal-shield.js" in landing
    dash = (root / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "legal-shield.js" in dash


def test_sanitize_oracle_includes_shield():
    from security_sanitize import sanitize_oracle_payload

    out = sanitize_oracle_payload({"verdict": "BUY", "oracle": "Bullish analytics on ETH"})
    assert "disclaimer" in out
    assert out["oracle"].startswith("DISCLAIMER:")
    assert out["system_classification"] == "analytical_tool"
