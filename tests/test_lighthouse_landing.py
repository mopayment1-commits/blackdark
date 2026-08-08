"""Lighthouse closure guards for the public landing page."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_robots_txt_uses_absolute_sitemap(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark.io")
    from dashboard import app

    client = TestClient(app)
    res = client.get("/robots.txt")
    assert res.status_code == 200
    body = res.text
    assert "Sitemap: https://blackdark.io/sitemap.xml" in body
    assert "Sitemap: /sitemap.xml" not in body


def test_landing_html_a11y_and_perf_hooks():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert '<main id="main">' in html
    assert 'class="skip-link"' in html
    assert 'for="landingAudience"' in html
    assert 'for="landingUxMode"' in html
    assert "fonts.googleapis.com" not in html
    assert "/static/fonts.css" in html
    assert "/static/landing.css" in html
    assert "/static/landing.js" in html
    assert 'src="/static/landing.js" defer' in html
    # Heading order: demos are h2 under page h1
    assert "<h2>📱 Telegram Free Alerts</h2>" in html
    assert "<h2>BLACKDARK Oracle</h2>" in html
    assert "<h3>Share Your Signal</h3>" in html


def test_landing_assets_exist_and_js_has_no_duplicate_action():
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "landing.css").read_text(encoding="utf-8")
    js = (root / "static" / "landing.js").read_text(encoding="utf-8")
    fonts_css = (root / "static" / "fonts.css").read_text(encoding="utf-8")
    font_file = root / "static" / "fonts" / "inter-latin.woff2"

    assert font_file.is_file() and font_file.stat().st_size > 10_000
    assert "font-display:swap" in fonts_css.replace(" ", "") or "font-display: swap" in fonts_css
    assert "--text-muted:#a1a1aa" in css.replace(" ", "")
    assert "const action" in js
    # Second declaration must not reintroduce SyntaxError
    assert js.count("const action") == 1
    assert "systemAction" in js
    assert "requestIdleCallback" in js
    assert "IntersectionObserver" in js


def test_static_landing_assets_served():
    from dashboard import app

    client = TestClient(app)
    for path in (
        "/static/landing.css",
        "/static/landing.js",
        "/static/fonts.css",
        "/static/fonts/inter-latin.woff2",
        "/favicon.ico",
        "/static/icon-192.png",
    ):
        res = client.get(path)
        assert res.status_code == 200, path
