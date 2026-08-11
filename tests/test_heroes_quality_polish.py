"""Six Heroes quality polish — expert acceptance bars."""

from __future__ import annotations

from pathlib import Path


def test_decision_certificate_export_and_verify():
    from decision_certificate import build_decision_certificate

    cert = build_decision_certificate(
        {
            "symbol": "BTC",
            "prediction_id": 42,
            "chain_hash": "abc123",
            "decision_action": "ACT",
            "decision_sentence": "ACT on BTC — score 70.",
            "opportunity_score": 70,
            "net_edge_truth": {"truth_score": 61},
            "opportunity_half_life": {"expected_half_life_seconds": 120},
            "market_regime": "trend",
            "ux_mode": "pro",
        }
    )
    assert cert["certificate_hash"]
    assert cert["export_text"]
    assert "BLACKDARK Decision Certificate" in cert["export_text"]
    assert cert["verify_url"]
    assert "whatsapp" in cert["share_urls"]
    assert cert["permalink"]


def test_oqs_why_under_five_seconds():
    from heroes_quality import build_oqs_why_block

    block = build_oqs_why_block(
        {
            "explanation": {
                "top_3_factors": [
                    {"factor": "Momentum", "detail": "RSI 62", "source": "binance"},
                    {"factor": "Flow", "detail": "quiet", "source": "cvvd"},
                    {"factor": "Sentiment", "detail": "neutral", "source": "news"},
                ]
            }
        }
    )
    assert block["ready"] is True
    assert len(block["top_3_factors"]) == 3
    assert "five seconds" in block["grasp_line"].lower() or "Top 3" in block["grasp_line"]
    assert "Momentum" in block["why_text"]


def test_ledger_share_kit():
    from heroes_quality import build_ledger_share_kit

    kit = build_ledger_share_kit(accuracy_pct=61.5, total_predictions=120)
    assert "oracle-accuracy" in kit["url"]
    assert "misses" in kit["share_text"].lower()
    assert "x" in kit["share_urls"]
    assert "telegram" in kit["share_urls"]


def test_portfolio_one_sentence():
    from heroes_quality import build_portfolio_clarity

    clarity = build_portfolio_clarity(
        {
            "risk_level": "HIGH",
            "risk_score": 8,
            "btc_beta_weighted": 0.9,
            "estimated_loss_formatted": "$12,000",
            "scenario_btc_drop_pct": 15,
            "total_value_formatted": "$100,000",
            "plain_language": "In plain language: high risk.",
        }
    )
    assert "high risk" in clarity["one_sentence"].lower()
    assert clarity["ready"] is True


def test_glass_box_operator_runbook():
    from glass_box_challenge import build_glass_box_challenge_pack, build_glass_box_operator_pack

    pack = build_glass_box_challenge_pack()
    assert "operator_runbook" in pack
    assert len(pack["operator_runbook"]["gates"]) >= 4
    assert pack["operator_runbook"]["t_minus_checklist"]
    op = build_glass_box_operator_pack()
    assert op["operator_runbook"]["machine_ready"] is True


def test_heroes_quality_manifest_six_only():
    from heroes_quality import heroes_quality_manifest

    m = heroes_quality_manifest()
    assert len(m["heroes"]) == 6
    assert "viral_arena" in m["not_building"]
    assert "browser_extension_platform" in m["not_building"]


def test_whale_one_sentence_field_shape():
    from whale_signal_classifier import classify_whale_alert

    row = classify_whale_alert(
        {
            "asset": "ETH",
            "direction": "in",
            "amount_usd": 5_000_000,
            "detail": "cold wallet custody move",
            "exchange": "coinbase",
        }
    )
    assert row["label"] in {"SIGNAL", "NOISE"}
    assert row["sentence"]
    assert "custody" in row["class_id"] or "NOISE" in row["label"]


def test_ui_wires_quality_polish():
    root = Path(__file__).resolve().parents[1]
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    assert "oqs_why" in landing
    assert "Download TXT" in landing or "dlCertTxtBtn" in landing
    assert "preferQuick" in landing or "/quick" in landing
    dash = (root / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "one_sentence" in dash
    assert "under five seconds" in dash
    acc = (root / "templates" / "oracle_accuracy.html").read_text(encoding="utf-8")
    assert "ledger/share-kit" in acc or "loadLedgerShareKit" in acc
    assert "operator" in acc.lower()
    assert (root / "docs" / "GLASS_BOX_OPERATOR_RUNBOOK.md").is_file()


def test_heroes_router_quality_endpoints_importable():
    from api.routers import heroes as heroes_router

    paths = {getattr(r, "path", None) for r in heroes_router.router.routes}
    assert "/api/heroes/quality" in paths
    assert "/api/ledger/share-kit" in paths
    assert "/api/glass-box/operator" in paths
