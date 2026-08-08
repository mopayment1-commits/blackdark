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
    assert 'class="skip-link"' in html or 'Skip to Trust Pulse' in html
    assert 'for="landingAudience"' in html
    assert 'for="landingUxMode"' in html
    assert "/static/css/trust-os.css" in html
    assert "We publish the miss" in html
    assert "/static/img/blackdark-sealed-hero.png" in html



def test_landing_assets_exist_and_design_tokens():
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "css" / "trust-os.css").read_text(encoding="utf-8")
    hero = root / "static" / "img" / "blackdark-sealed-hero.png"
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    assert hero.is_file() and hero.stat().st_size > 50_000
    assert "--bd-muted-dim: #a1a1aa" in css or "--bd-muted: #a1a1aa" in css
    assert landing.count("const action =") <= 1
    assert 'for="landingAudience"' in landing


def test_static_landing_assets_served():
    from dashboard import app

    client = TestClient(app)
    for path in (
        "/static/css/trust-os.css",
        "/static/img/blackdark-sealed-hero.png",
        "/favicon.ico",
        "/static/icon-192.png",
    ):
        res = client.get(path)
        assert res.status_code == 200, path

