"""B2B public page must not show placeholder API keys in WebSocket URL."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_b2b_page_ws_line_has_no_api_key_query(monkeypatch):
    monkeypatch.delenv("EXPOSE_B2B_DEMO_KEY", raising=False)
    from dashboard import app

    client = TestClient(app)
    page = client.get("/b2b")
    assert page.status_code == 200
    assert "contact-sales" not in page.text
    assert "api_key=contact-sales" not in page.text
    start = page.text.find('id="wsEndpointLine"')
    assert start != -1
    end = page.text.find("</pre>", start)
    ws_line = page.text[start:end]
    assert "/ws/b2b/feed" in ws_line
    assert "api_key" not in ws_line
    assert "Load Public Summary" in page.text
    assert "disconnected" in page.text.lower() or 'id="wsStatus">disconnected' in page.text
