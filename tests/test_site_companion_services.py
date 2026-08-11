from __future__ import annotations

import pytest

"""Companion site services — footer, legal hub, FAQ, status, feedback, AI Chat UI."""


from pathlib import Path


def test_site_services_manifest():
    from site_services import (
        FAQ_ITEMS,
        HOW_IT_WORKS_STEPS,
        brand_social,
        footer_manifest,
        legal_hub_manifest,
        public_status_report,
        site_services_manifest,
    )

    m = site_services_manifest()
    assert m["product"] == "BLACKDARK Trust OS"
    assert m["ai_chat"]["free_tier"] is False
    assert "pro" in m["ai_chat"]["tiers"]
    assert FAQ_ITEMS
    assert HOW_IT_WORKS_STEPS
    foot = footer_manifest()
    assert any(x["href"] == "/legal" for x in foot["legal"])
    assert any(x["href"] == "/faq" for x in foot["trust"])
    assert brand_social()
    hub = legal_hub_manifest()
    assert any(p["href"] == "/cookies" for p in hub["pages"])
    status = public_status_report()
    assert status["honesty"]["secrets_exposed"] is False
    assert "components" in status


def test_feedback_submit(tmp_path, monkeypatch):
    import site_services as ss

    monkeypatch.setattr(ss, "_FEEDBACK_PATH", tmp_path / "feedback.jsonl")

    def _no_email(*_a, **_k):
        return {"id": "eml_test"}

    monkeypatch.setattr("email_outbox.enqueue_email", _no_email, raising=False)
    try:
        import email_outbox

        monkeypatch.setattr(email_outbox, "enqueue_email", _no_email)
    except Exception:
        pass

    out = ss.submit_feedback(
        category="suggestion",
        message="Please add clearer Why on mobile proof cards.",
        email="tester@example.com",
        page="/feedback",
    )
    assert out["ok"] is True
    assert out["id"].startswith("fb_")
    assert (tmp_path / "feedback.jsonl").is_file()

    with pytest.raises(ValueError):
        ss.submit_feedback(category="x", message="short")


def test_cookies_legal_page():
    from legal_content import LEGAL_PAGES

    assert "cookies" in LEGAL_PAGES
    assert "localStorage" in LEGAL_PAGES["cookies"]["html"]


def test_templates_wire_companion_surfaces():
    dash = Path("templates/dashboard.html").read_text(encoding="utf-8")
    land = Path("templates/landing.html").read_text(encoding="utf-8")
    util = Path("templates/utility.html").read_text(encoding="utf-8")
    foot = Path("templates/partials/site_footer.html").read_text(encoding="utf-8")
    assert 'id="ai-chat"' in dash
    assert "sendChat" in dash
    assert "partials/site_footer.html" in dash
    assert "partials/site_footer.html" in land
    assert "Follow us" in foot
    assert "page == 'faq'" in util
    assert "page == 'legal_hub'" in util
    assert "page == 'status'" in util
    assert "page == 'cancel'" in util
    assert Path("docs/SITE_COMPANION_SERVICES.md").is_file()


def test_dashboard_routes_registered():
    src = Path("dashboard.py").read_text(encoding="utf-8")
    for path in (
        '"/legal"',
        '"/faq"',
        '"/how-it-works"',
        '"/about"',
        '"/status"',
        '"/changelog"',
        '"/feedback"',
        '"/cookies"',
        '"/api/site-services"',
        '"/api/feedback"',
        '"/api/status"',
    ):
        assert path in src


def test_chat_prompt_not_guaranteed_advice():
    src = Path("chat_service.py").read_text(encoding="utf-8")
    low = src.lower()
    assert "not replace the oracle" in low
    assert "never guarantee" in low


def test_ai_chat_tier_gate():
    from auth_service import TIER_FEATURES

    assert TIER_FEATURES["free"].get("ai_chat") is False
    assert TIER_FEATURES["pro"].get("ai_chat") is True
    assert TIER_FEATURES["whale"].get("ai_chat") is True
