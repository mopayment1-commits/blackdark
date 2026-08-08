"""Third-pass gates: Language / Login / Sign up / Pricing must be USER-VISIBLE."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def _landing() -> str:
    return (ROOT / "templates/landing.html").read_text(encoding="utf-8")


def test_landing_utility_chrome_outside_collapsible_nav_links():
    land = _landing()
    assert "partials/top_utility.html" in land
    # Language/Login must NOT sit only inside .nav-links (mobile hides that).
    nav_links_block_start = land.find('<div class="nav-links">')
    nav_links_block_end = land.find("</div>", nav_links_block_start)
    block = land[nav_links_block_start:nav_links_block_end]
    assert "top_utility" not in block
    assert "lang_switcher" not in block
    assert "nav-right" in land
    assert "/* Hide lens marketing links only" in land or "NEVER hide Language" in land


def test_top_utility_has_lang_login_signup_pricing():
    util = (ROOT / "templates/partials/top_utility.html").read_text(encoding="utf-8")
    assert "lang_switcher.html" in util
    assert "/login" in util
    assert "/login?tab=register" in util
    assert "/#pricing" in util
    assert "bd-top-utility" in util


def test_lang_switcher_lists_fifteen_locales():
    sw = (ROOT / "templates/partials/lang_switcher.html").read_text(encoding="utf-8")
    for code in (
        "en",
        "zh-CN",
        "hi",
        "ja",
        "ko",
        "ru",
        "pt",
        "es",
        "fr",
        "de",
        "ar",
        "tr",
        "vi",
        "id",
        "th",
    ):
        assert code in sw
    # Must render even without template context
    assert "_locales" in sw


def test_login_has_register_tab_and_top_chrome():
    login = (ROOT / "templates/login.html").read_text(encoding="utf-8")
    assert 'id="tabRegister"' in login
    assert "top_utility.html" in login
    assert "login-chrome" in login
    assert "doRegister" in login
    assert "accepted_terms" in login


def test_profile_has_lang_billing_and_signup_gate():
    profile = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    assert "top_utility.html" in profile
    assert 'lang="{{ lang|default(\'en\') }}"' in profile or 'lang="{{ lang|default(' in profile
    assert "create-checkout-session?tier=pro" in profile
    assert "create-checkout-session?tier=whale" in profile
    assert "Decision Desk $49" in profile
    assert "tab=register" in profile
    assert "billingReady" in profile


def test_dashboard_and_accuracy_include_top_utility():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    acc = (ROOT / "templates/oracle_accuracy.html").read_text(encoding="utf-8")
    assert "top_utility.html" in dash
    assert "top_utility.html" in acc


def test_pricing_ladder_visible_on_landing():
    land = _landing()
    assert "Decision Desk" in land
    assert "$49" in land
    assert "$29" in land
    assert "pricing.from_open" in land or "From $3,000" in land or "3,000" in land
    assert "Whale Desk" not in land
    assert "$199" not in land
    assert "billingReadyLine" in land
    assert "/login?tab=register" in land
