"""About page — h1 uses site accent cyan."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dashboard import app


def test_about_page_has_accent_heading_class():
    client = TestClient(app)
    res = client.get("/about", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'class="page-about"' in res.text or "page-about" in res.text
    assert "body.page-about h1" in res.text or "About BLACKDARK" in res.text
