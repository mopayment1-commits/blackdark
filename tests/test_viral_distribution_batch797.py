"""Tests — #797 Viral Intelligence Distribution Loop."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_radar_indicators as mri
from bd_platform import viral_intelligence_distribution_loop as vid


@pytest.fixture
def vid_seed() -> dict:
    return json.loads(Path("data/viral_intelligence_distribution_loop_seed.json").read_text(encoding="utf-8"))


def test_797_status():
    status = vid.viral_intelligence_distribution_status_797()
    assert status["standalone_rejected"] is True
    assert status["rule_based_share_detection"] is True
    assert status["no_auto_posting"] is True
    assert status["no_share_to_trade"] is True
    assert status["evidence_layer_ref"] == 777


def test_797_share_worthy_volatility(vid_seed):
    event = vid_seed["market_events"][0]
    det = vid.detect_share_worthy_event_797(event, seed=vid_seed)
    assert det["share_worthy"] is True
    assert "volatility_1h>5" in det["triggers"][0]


def test_797_share_worthy_news(vid_seed):
    event = vid_seed["market_events"][1]
    det = vid.detect_share_worthy_event_797(event, seed=vid_seed)
    assert det["share_worthy"] is True
    assert "news_event" in det["triggers"]


def test_797_not_share_worthy(vid_seed):
    event = vid_seed["market_events"][2]
    det = vid.detect_share_worthy_event_797(event, seed=vid_seed)
    assert det["share_worthy"] is False


def test_797_evidence_card(vid_seed):
    card = vid.build_shareable_intelligence_card_797(
        "evt-btc-vol-001",
        user_tier="free",
        user_state=vid_seed["user_states"]["default"],
        seed=vid_seed,
    )
    assert card["ok"] is True
    assert "evidence_confidence_777" in card
    assert card["no_unsupported_claims"] is True
    assert "Source:" in card["headline"]
    assert "exploding" not in card["headline"].lower()
    assert card["source_timestamp"]
    assert card["freshness_sec"] is not None


def test_797_factual_headline_no_hype(vid_seed):
    card = vid.build_shareable_intelligence_card_797(
        "evt-btc-vol-001",
        user_state=vid_seed["user_states"]["default"],
        seed=vid_seed,
    )
    check = vid._validate_no_unsupported_claims("Bitcoin exploding! Buy now!", seed=vid_seed)
    assert check["valid"] is False
    assert card["headline_ar_label"] == "بيانات موثقة"


def test_797_entitlement_free_vs_pro(vid_seed):
    free = vid.check_share_entitlement_797("free", seed=vid_seed)
    pro = vid.check_share_entitlement_797("pro", seed=vid_seed)
    assert free["card_level"] == "basic"
    assert pro["card_level"] == "detailed"
    assert "metrics" in pro["allowed_fields"] or "evidence_chain" in pro["allowed_fields"]


def test_797_consent_required(vid_seed):
    no_consent = vid.check_share_consent_797(vid_seed["user_states"]["no_consent"], seed=vid_seed)
    assert no_consent["consent_required"] is True
    assert no_consent["tracking_allowed"] is False


def test_797_rate_limit(vid_seed):
    rate = vid.check_share_rate_limit_797(vid_seed["user_states"]["rate_limited"], seed=vid_seed)
    assert rate["allowed"] is False
    blocked = vid.build_shareable_intelligence_card_797(
        "evt-btc-vol-001",
        user_state=vid_seed["user_states"]["rate_limited"],
        seed=vid_seed,
    )
    assert blocked["error"] == "rate_limited"


def test_797_deep_link(vid_seed):
    link = vid.build_deep_link_797("evt-btc-vol-001", "ref-test-001", seed=vid_seed)
    assert link["deep_link_path"] == "/radar/event/evt-btc-vol-001"
    assert "ref=ref-test-001" in link["deep_link_url"]
    assert link["no_separate_landing"] is True


def test_797_channel_outputs(vid_seed):
    card = vid.build_shareable_intelligence_card_797(
        "evt-btc-vol-001",
        user_state=vid_seed["user_states"]["default"],
        seed=vid_seed,
    )
    outputs = card["channel_outputs"]
    assert "x" in outputs
    assert "telegram" in outputs
    assert "discord" in outputs
    assert outputs["no_auto_posting"] is True


def test_797_attribution_funnel(vid_seed):
    evt = vid.record_attribution_event_797(
        "signup", referral_id="ref-test", event_id="evt-btc-vol-001", seed=vid_seed,
    )
    assert evt["ok"] is True
    assert evt["attribution_integrity"] is True
    summary = vid.build_attribution_funnel_summary_797(seed=vid_seed)
    assert summary["reshare_loop_active"] is True


def test_797_landing_widget(vid_seed):
    widget = vid.build_landing_viral_share_widget_797(seed=vid_seed)
    assert widget["surface"] == "landing_page"
    assert widget["cta_ar"] == "اكتشف المزيد"
    assert widget["extends_existing_share_buttons"] is True
    assert widget["card"]["ok"] is True


def test_797_market_radar_share(vid_seed):
    action = vid.build_market_radar_share_action_797("BTC", seed=vid_seed)
    assert action["action_label_ar"] == "مشاركة"
    assert action["shareable_event_count"] >= 1
    assert action["primary_card"]["ok"] is True


def test_797_event_landing_context(vid_seed):
    ctx = vid.build_event_landing_context_797("evt-btc-vol-001", "ref-visit-001", seed=vid_seed)
    assert ctx["ok"] is True
    assert ctx["free_experience"] is True


def test_797_e2e_loop(vid_seed):
    e2e = vid.run_viral_distribution_e2e_797(seed=vid_seed)
    assert e2e["all_passed"] is True


def test_797_market_radar_integration():
    panel = mri.build_market_radar_panel("BTC")
    share = panel.get("viral_share_action_797") or {}
    assert share.get("ok") is True


def test_797_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/viral-loop/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/viral-loop/share?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["action_label_ar"] == "مشاركة"
    e2e = c.get("/api/platform/intelligence-ledger/viral-loop/e2e")
    assert e2e.status_code == 200
    assert e2e.json()["all_passed"] is True
