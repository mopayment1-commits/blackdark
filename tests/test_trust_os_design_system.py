"""Trust OS Design System v1 — palette, type, motions, anti-patterns."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def test_design_system_css_and_doc():
    css = (ROOT / "static/css/trust-os.css").read_text(encoding="utf-8")
    doc = (ROOT / "docs/TRUST_OS_DESIGN_SYSTEM.md").read_text(encoding="utf-8")
    assert "--bd-bg: #0a0a0f" in css or "--bd-bg:#0a0a0f" in css.replace(" ", "")
    assert "--bd-accent: #22d3ee" in css or "#22d3ee" in css
    assert "Syne" in css
    assert "IBM Plex Sans" in css
    assert "bdPulseIn" in css and "bdFlipFlash" in css and "bdSharePop" in css
    assert "Inter" not in css.split("REJECTED")[0] or "REJECTED" in css
    assert "ARENA" in doc or "arena" in doc.lower()
    assert "Fake scarcity" in doc or "fake scarcity" in doc.lower()
    assert "$29" in doc and "$49" in doc


def test_templates_link_design_system():
    pages = [
        "templates/landing.html",
        "templates/dashboard.html",
        "templates/utility.html",
        "templates/legal.html",
        "templates/login.html",
        "templates/success.html",
        "templates/oracle_accuracy.html",
        "templates/profile.html",
        "templates/reset_password.html",
        "templates/b2b.html",
        "templates/platform.html",
        "templates/discipline.html",
        "templates/coin.html",
    ]
    for path in pages:
        src = (ROOT / path).read_text(encoding="utf-8")
        assert "/static/css/trust-os.css" in src, path


def test_landing_rejects_inter_purple_and_keeps_pricing_canon():
    land = (ROOT / "templates/landing.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com/css2?family=Inter" not in land
    assert "#a78bfa" not in land
    assert "#f472b6" not in land
    assert "Decision Pro" in land and "$29" in land
    assert "Decision Desk" in land and "$49" in land
    assert "$199" not in land
    assert "pricing.cta.talk" in land or "pricing.from_open" in land or "institutionalInquiryForm" in land
    assert 'id="trust-pulse"' in land
    assert "waitlist.sub" in land or "fake seat" in land.lower()
    assert "🎁" not in land
    assert 'class="launch-banner"' not in land
    assert 'has-launch-banner' not in land
    assert 'id="landingStats"' in land
    # Stats must sit after Trust Pulse (not in first composition)
    pulse_i = land.find('id="trust-pulse"')
    stats_i = land.find('id="landingStats"')
    assert 0 <= pulse_i < stats_i
    assert "BLACKDARK" in land
    # Copy lives in i18n keys (rendered via t()) — template must wire them.
    assert "hero.headline" in land and "hero.support" in land
    assert "hero.cta.try" in land and "hero.cta.seal" in land
    assert "blackdark-sealed-hero-1280.webp" in land
    assert "blackdark-sealed-hero.jpg" in land
    assert "hero-bleed" in land
    assert 'id="seal"' in land
    # Sealed myth + Trust Pulse share one first composition
    hero_i = land.find('id="top"')
    comp_i = land.find('class="hero-composition"')
    pulse_i = land.find('id="trust-pulse"')
    seal_i = land.find('id="seal"')
    assert 0 <= hero_i < comp_i < pulse_i < seal_i
    composition = land[comp_i:seal_i]
    assert 'id="trust-pulse"' in composition
    assert "hero.cta.try" in composition
    assert "hero.cta.seal" in composition
    # Rendered English still carries the brand sentences for real visitors.
    from fastapi.testclient import TestClient

    from dashboard import app

    html = TestClient(app).get("/").text
    assert "Decide. Prove it. Share it." in html
    assert "We publish the miss." in html
    assert "Try Oracle Free" in html
    orphan = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com/css2?family=Inter" not in orphan
    assert "#a78bfa" not in orphan
    assert "Inter" not in orphan
    assert (ROOT / "static/img/blackdark-sealed-hero-1280.webp").is_file()
    assert (ROOT / "static/img/blackdark-sealed-hero.jpg").is_file()


def test_trust_os_manifest_includes_design_system():
    from trust_os import trust_os_manifest

    m = trust_os_manifest()
    assert m["design_system"]["css"] == "/static/css/trust-os.css"
    assert "docs/TRUST_OS_DESIGN_SYSTEM.md" in m["binding_docs"]
    assert "arena" in m["design_system"]["rejected"]
