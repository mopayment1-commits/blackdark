"""Trial persona readiness — six audiences, honest entitlements."""

from __future__ import annotations


def test_six_audiences_routed():
    from audience_routing import all_audiences, normalize_audience

    assert normalize_audience("b2b") == "b2b"
    assert normalize_audience("acquisition") == "acquirer"
    ids = [a["audience"] for a in all_audiences()]
    assert ids == ["retail", "pro", "whale", "fund", "b2b", "acquirer"]


def test_persona_capability_matrix_honest():
    from persona_capability_matrix import persona_capability_matrix

    out = persona_capability_matrix()
    assert out["ok"] is True
    assert out["product_complete"] is False
    assert out["institutional_verdict"] == "NOT_COMPLETE"
    assert out["live_money_ready"] is False
    assert set(out["personas"]) == {"retail", "pro", "whale", "fund", "b2b", "acquirer"}
    whale = out["personas"]["whale"]
    live = [c for c in whale["gets"] if c["name"] == "Live venue FILL"][0]
    assert live["status"] == "external_block"
    assert out["four_blockers"]["live_fill"] is False
    assert out["four_blockers"]["jupiter_vc"] is False
    assert out["four_blockers"]["full_mesh_l2_complete"] is False
    assert out["four_blockers"]["cloud_multi_az"] is False


def test_org_scoped_b2b_feed_key():
    from org_tenant import create_org, issue_org_feed_key, verify_org_feed_key
    from whale_tracker import InstitutionalDataExporter

    org = create_org(name="Trial B2B Co", owner_email="owner@example.com")
    issued = issue_org_feed_key(org["org_id"], actor_email="owner@example.com")
    assert issued["api_key"].startswith("bd_org_")
    hit = verify_org_feed_key(issued["api_key"])
    assert hit and hit["org_id"] == org["org_id"]
    assert verify_org_feed_key("bd_org_not_a_real_key_value_xxx") is None
    exp = InstitutionalDataExporter(api_key="")
    assert exp.authorize(issued["api_key"]) is True
    assert exp.authorize("wrong") is False


def test_mfa_copy_points_at_profile():
    from auth_service import TIER_FEATURES
    import auth_service
    import inspect

    src = inspect.getsource(auth_service)
    assert "/settings/security" not in src
    assert "/profile" in src
    assert "free" in TIER_FEATURES
