"""Launch readiness: constitution path wired on primary Oracle + auth gates."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_decision_enrichment_attaches_constitution_fields():
    from decision_enrichment import enrich_oracle_decision

    payload = enrich_oracle_decision(
        {
            "symbol": "BTC",
            "opportunity_score": 72,
            "verdict": "BUY",
            "price": 65000,
            "volume_24h": 1_000_000,
            "market_regime": "risk_on",
        },
        ux_mode="pro",
        lang="ar",
        register_signal=True,
    )
    assert payload.get("net_edge_truth")
    assert payload.get("opportunity_half_life")
    assert payload.get("persona_clarity")
    assert payload.get("signal_registry", {}).get("signal_id")
    assert payload.get("decision_sentence")
    assert payload.get("ux_mode") == "pro"


def test_beginner_ux_hides_pro_internals():
    from decision_enrichment import enrich_oracle_decision

    payload = enrich_oracle_decision(
        {
            "symbol": "ETH",
            "opportunity_score": 61,
            "verdict": "WAIT",
            "price": 3200,
            "volume_24h": 500_000,
        },
        ux_mode="beginner",
        lang="ar",
        register_signal=False,
    )
    assert payload["ux_mode"] == "beginner"
    assert "decision_sentence" in payload
    assert "upgrade_hint" in payload
    # Pro-only economics should not dominate beginner surface
    assert "modal_breakdown" not in payload


def test_whale_tier_has_b2b_and_evidence():
    from auth_service import TIER_FEATURES

    assert TIER_FEATURES["whale"]["b2b_api"] is True
    assert TIER_FEATURES["whale"]["evidence_pack"] is True
    assert TIER_FEATURES["free"]["b2b_api"] is False


def test_admin_launch_template_exists():
    assert (ROOT / "templates" / "admin_launch.html").is_file()


def test_runbook_and_constitution_exist():
    assert (ROOT / "docs" / "RUNBOOK.md").is_file()
    assert (ROOT / "docs" / "PRODUCT_CONSTITUTION_AR.md").is_file()


def test_finalize_and_secrets_scripts_exist():
    assert (ROOT / "scripts" / "finalize_launch.py").is_file()
    assert (ROOT / "scripts" / "generate_launch_secrets.py").is_file()
    assert ".env.launch.local" in (ROOT / ".gitignore").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_evidence_pack_marks_d5_honestly():
    from acquirer_evidence_pack import build_acquirer_evidence_pack

    pack = await build_acquirer_evidence_pack()
    d5 = next(d for d in pack["differentiators"] if d["id"] == "D5")
    assert d5["status"] == "weights_live"


def test_launch_checklist_includes_constitution_gate():
    from launch_checklist import _checklist_rows

    ids = {r["id"] for r in _checklist_rows()}
    assert "d5_constitution" in ids
    assert "d5_evidence_auth" in ids


def test_public_accuracy_exposes_prediction_id_shape():
    # Unit-level shape: recent builder fields present in source
    src = (ROOT / "ml" / "public_accuracy.py").read_text(encoding="utf-8")
    assert "prediction_id" in src
    assert "proof_chain" in src or "_proof_chain_block" in src


@pytest.mark.asyncio
async def test_regime_router_attaches_regime():
    from ml.regime_router import predict_direction_regime_aware

    out = await predict_direction_regime_aware("BTC", price=65000.0, change_24h=1.0)
    assert "market_regime" in out
    assert out.get("regime_router", {}).get("per_regime_models") is False
