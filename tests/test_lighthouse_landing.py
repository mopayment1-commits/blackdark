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
    assert "/static/img/blackdark-sealed-hero-1280.webp" in html
    assert "/static/img/blackdark-sealed-hero.jpg" in html
    assert 'rel="preload"' in html and "blackdark-sealed-hero-1280.webp" in html


def test_landing_assets_exist_and_design_tokens():
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "css" / "trust-os.css").read_text(encoding="utf-8")
    hero_webp = root / "static" / "img" / "blackdark-sealed-hero-1280.webp"
    hero_jpg = root / "static" / "img" / "blackdark-sealed-hero.jpg"
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    assert hero_webp.is_file() and hero_webp.stat().st_size < 120_000
    assert hero_jpg.is_file() and hero_jpg.stat().st_size < 200_000
    assert "--bd-muted-dim: #a1a1aa" in css or "--bd-muted: #a1a1aa" in css
    assert landing.count("const action =") <= 1
    assert 'for="landingAudience"' in landing


def test_static_landing_assets_served():
    from dashboard import app

    client = TestClient(app)
    for path in (
        "/static/css/trust-os.css",
        "/static/img/blackdark-sealed-hero-1280.webp",
        "/static/img/blackdark-sealed-hero.webp",
        "/static/img/blackdark-sealed-hero.jpg",
        "/favicon.ico",
        "/static/icon-192.png",
    ):
        res = client.get(path)
        assert res.status_code == 200, path


def test_landing_html_ttfb_under_200ms():
    """Server-side landing TTFB must stay well under the 200ms product bar."""
    import time

    from dashboard import app

    client = TestClient(app)
    client.get("/")  # warm Jinja + middleware
    samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = client.get("/")
        samples.append((time.perf_counter() - t0) * 1000)
        assert res.status_code == 200
    # Median keeps CI noise low while still enforcing a strict bar.
    samples.sort()
    median = samples[len(samples) // 2]
    assert median < 200, f"landing median {median:.1f}ms samples={samples}"

