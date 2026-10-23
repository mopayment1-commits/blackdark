"""WCAG validator-oriented guards for the public landing page."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def _landing_html() -> str:
    from dashboard import app

    res = TestClient(app).get("/")
    assert res.status_code == 200
    return res.text


def test_muted_tokens_aa_safe_on_landing():
    html = _landing_html()
    assert "body.landing-page" in html or 'class="landing-page"' in html
    assert "#c8c8d0" in html
    assert html.count("#71717a") == 0


def test_no_prohibited_aria_live_on_dialog_or_status():
    html = _landing_html()
    assert 'role="dialog"' in html
    for m in re.finditer(r'<[^>]+role="dialog"[^>]*>', html, flags=re.I):
        assert "aria-live" not in m.group(0).lower()
    assert 'role="status" aria-live' not in html.replace(" ", "").lower()


def test_lang_and_symbol_selects_use_label_not_duplicate_aria():
    html = _landing_html()
    assert 'for="bdLangTrigger"' in html
    lang_sel = re.search(r'<select[^>]*id="bdLangTrigger"[^>]*>', html)
    assert lang_sel and "aria-label" not in lang_sel.group(0)
    sym_sel = re.search(r'<select[^>]*id="symbol"[^>]*>', html)
    assert sym_sel and "aria-label" not in sym_sel.group(0)
    assert 'for="symbol"' in html


def test_account_menu_haspopup_valid_value():
    html = _landing_html()
    assert 'aria-haspopup="menu"' not in html
    if 'id="bdAccountTrigger"' in html:
        assert 'aria-haspopup="true"' in html


def test_inline_footer_links_distinguished():
    html = _landing_html()
    assert "bd-foot-bottom a" in html
    assert "text-decoration: underline" in html


def test_share_modal_has_valid_dialog_label():
    html = _landing_html()
    assert 'id="bdShareDecisionTitle"' in html
    assert 'aria-labelledby="bdShareDecisionTitle"' in html
