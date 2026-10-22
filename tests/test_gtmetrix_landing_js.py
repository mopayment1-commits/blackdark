"""GTmetrix / TBT guards — landing JS split and lazy nav scripts."""

from __future__ import annotations

from pathlib import Path


def test_landing_uses_light_boot_entry_and_main_chunk():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'defer src="/static/js/landing_boot.js"' in landing
    assert "landing_boot_main.js" not in landing
    assert "csrf_fetch.js" not in landing
    assert Path("static/js/landing_boot_main.js").is_file()
    entry = Path("static/js/landing_boot.js").read_text(encoding="utf-8")
    assert "landing_boot_main.js" in entry
    assert "bd_live_refresh.js" not in entry
    assert len(entry) < 8000
    main = Path("static/js/landing_boot_main.js").read_text(encoding="utf-8")
    assert "ensureLiveRefreshModule" in main


def test_landing_nav_lazy_scripts():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    nav = Path("templates/partials/site_top_nav.html").read_text(encoding="utf-8")
    assert "landing_lazy_scripts" in landing
    assert "landing_nav_lazy.js" in nav
    assert "bd_lazy_script.js" in nav


def test_main_deferred_oracle_boot():
    main = Path("static/js/landing_boot_main.js").read_text(encoding="utf-8")
    assert "scheduleDeferredOracleBoot" in main
    assert "IntersectionObserver" in main
