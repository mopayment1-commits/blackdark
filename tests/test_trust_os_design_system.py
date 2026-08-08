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
    assert "$29" in doc and "$199" in doc


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
    assert "Whale Desk" in land and "$199" in land
    assert "Talk to us" in land
    assert 'id="trust-pulse"' in land
    assert "fake seat" in land.lower() or "No fake seat" in land
    # Brand is hero-level
    assert "BLACKDARK" in land
    assert "Decide. Prove it. Share it." in land


def test_trust_os_manifest_includes_design_system():
    from trust_os import trust_os_manifest

    m = trust_os_manifest()
    assert m["design_system"]["css"] == "/static/css/trust-os.css"
    assert "docs/TRUST_OS_DESIGN_SYSTEM.md" in m["binding_docs"]
    assert "arena" in m["design_system"]["rejected"]
