"""Third-pass gates: Language / Login / Sign up / Pricing must be USER-VISIBLE."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def _landing() -> str:
    return (ROOT / "templates/landing.html").read_text(encoding="utf-8")


def test_landing_uses_global_header_with_session_chrome():
    land = _landing()
    assert "partials/global_header.html" in land
    global_hdr = (ROOT / "templates/partials/global_header.html").read_text(encoding="utf-8")
    assert "bd-global-header" in global_hdr
    assert "bd-global-links" in global_hdr
    assert "top_utility.html" in global_hdr


def test_top_utility_has_anonymous_chrome_branches():
    util = (ROOT / "templates/partials/top_utility.html").read_text(encoding="utf-8")
    assert "lang_switcher.html" in util
    assert "/login" in util
    assert "/login?tab=register" in util
    assert 'id="bdUtilPricing"' in util
    assert "bd-header-util" in util
    assert "header_authenticated" in util
    assert "bd-tier-badge" in util
    assert "/profile" in util
    assert "bd-header-upgrade" not in util


def test_lang_switcher_lists_twenty_five_locales():
    sw = (ROOT / "templates/partials/lang_switcher.html").read_text(encoding="utf-8")
    for code in (
        "en",
        "es",
        "ar",
        "pt",
        "fr",
        "de",
        "zh-CN",
        "zh-TW",
        "ja",
        "ko",
        "hi",
        "tr",
        "ru",
        "id",
        "vi",
        "th",
        "fil",
        "it",
        "bn",
        "ur",
        "fa",
        "ms",
        "pl",
        "nl",
        "he",
    ):
        assert code in sw
    # Must render even without template context
    assert "_locales" in sw


def test_login_has_register_tab_and_global_header():
    login = (ROOT / "templates/login.html").read_text(encoding="utf-8")
    assert 'id="registerShell"' in login
    assert "global_header.html" in login
    assert 'class="login-main"' in login
    assert 'class="auth-tabs"' in login
    assert "bd-global-header .bd-header-util" in login
    assert "login-chrome" not in login
    assert "doRegister" in login
    assert "accepted_terms" in login


def test_profile_has_lang_billing_and_signup_gate():
    profile = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    assert "global_header.html" in profile
    assert 'lang="{{ lang|default(\'en\') }}"' in profile or 'lang="{{ lang|default(' in profile
    assert "create-checkout-session?tier=pro" in profile
    assert "create-checkout-session?tier=elite" in profile
    assert "SEE THE EDGE / ELITE $49.99" in profile
    assert "tab=register" in profile
    assert "billingReady" in profile


def test_dashboard_and_accuracy_include_global_header():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    acc = (ROOT / "templates/oracle_accuracy.html").read_text(encoding="utf-8")
    assert "global_header.html" in dash
    assert "global_header.html" in acc


def test_pricing_ladder_visible_on_landing():
    land = _landing()
    assert "pricing.decide_pro" in land
    assert "pricing.see_edge_elite" in land
    assert "pricing.execute_quant" in land
    assert "pricing.scale_institutional" in land
    assert "$19.99" in land
    assert "$49.99" in land
    assert "$129.99" in land
    assert "pricing.from_open" in land or "From $999" in land
    assert "Decision Desk" not in land
    assert "$29" not in land
    assert "3,000" not in land
    assert "pricing.popular" in land
    assert "billingReadyLine" in land
    assert "/login?tab=register" in land
