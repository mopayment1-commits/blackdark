"""Global chrome: nav search, Ask AI, public contact email."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_contact_page_shows_info_email():
    from dashboard import app

    page = TestClient(app).get("/contact")
    assert page.status_code == 200
    assert "info@blackdark.io" in page.text
    assert "mopayment1@gmail.com" not in page.text
    assert "complaints@blackdark.app" not in page.text


def test_nav_has_search_and_ask_ai_fab():
    from dashboard import app

    html = TestClient(app).get("/").text
    assert 'id="bdNavSearch"' in html
    assert 'id="bdAskAiToggle"' in html
    assert "Ask BLACKDARK AI" in html
    assert 'id="trust-pulse"' in html
    assert 'id="bdUtilPricing"' in html


def test_ask_ai_panel_hidden_rule_and_close_control():
    from pathlib import Path

    partial = Path("templates/partials/site_ask_ai.html").read_text(encoding="utf-8")
    assert 'id="bdAskAiClose"' in partial
    assert "Not financial advice." in partial
    assert ".bd-ask-ai-panel[hidden]" in partial
    assert "display: none !important" in partial
    js = Path("static/js/bd_site_assistant.js").read_text(encoding="utf-8")
    assert "function closePanel()" in js
    assert "toggle.focus()" in js


def test_site_assistant_refuses_financial_advice():
    from dashboard import app

    client = TestClient(app)
    res = client.post(
        "/api/public/site-assistant",
        json={"message": "Should I buy BTC now?", "page_context": {}},
    )
    assert res.status_code == 200
    assert res.json()["reply"] == "Not financial advice."
    assert res.json()["refusal"] is True


def test_site_search_finds_ledger():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/public/site-search", params={"q": "ledger"})
    assert res.status_code == 200
    paths = [r["path"] for r in res.json()["results"]]
    assert "/oracle-accuracy" in paths
