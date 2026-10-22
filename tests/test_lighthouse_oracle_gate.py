"""Landing Lighthouse fixes — oracle dedupe, auth gating, a11y hooks."""

from __future__ import annotations

from pathlib import Path


def test_landing_includes_oracle_fetch_gate_and_session_hint():
    nav = Path("templates/partials/site_top_nav.html").read_text(encoding="utf-8")
    assert "bd_oracle_fetch_gate.js" in nav
    assert "bd_session_hint.js" in nav


def test_watchlist_does_not_network_refresh_on_render():
    src = Path("static/js/bd_oracle_workspace.js").read_text(encoding="utf-8")
    assert "async function renderWatchlist(options)" in src
    assert "if (network) {" in src
    assert "await refreshWatchlistRow(sym)" in src


def test_landing_consult_oracle_boot_guard():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    boot = Path("static/js/landing_boot_main.js").read_text(encoding="utf-8")
    assert "landingOracleBootComplete" in boot
    assert "BDOracleFetchGate" in boot
    assert "BDSessionHint" in boot
    assert "landing-inline-link" in landing
    assert 'defer src="/static/js/landing_boot.js"' in landing


def test_lang_select_accessible_name():
    sw = Path("templates/partials/lang_switcher.html").read_text(encoding="utf-8")
    assert 'for="bdLangTrigger"' in sw
    assert "bd-lang-sr-only" in sw
    assert 'id="bdLangTrigger"' in sw


def test_social_heading_is_h3():
    html = Path("templates/partials/site_follow_social.html").read_text(encoding="utf-8")
    assert 'class="bd-social-heading"' in html and "<h3" in html
    assert "social_heading_id" in html
    assert "<h4 class=\"bd-social-heading\"" not in html
