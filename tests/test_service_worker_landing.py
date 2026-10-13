"""Service worker must not block document navigations (Lighthouse PAGE_HUNG)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from anonymous_route_foundation import is_anonymous_route_allowed


def test_sw_js_anonymous_get():
    assert is_anonymous_route_allowed("GET", "/sw.js") is True


def test_sw_does_not_intercept_html_navigate():
    src = Path("static/sw.js").read_text(encoding="utf-8")
    assert "if (isHtml) return" in src or "if (isHtml) {\n    return" in src
    assert "event.respondWith" in src
    # Document navigations must not use respondWith (only static assets).
    html_block = src.split("if (isHtml)", 1)[1].split("if (url.pathname.startsWith('/static/')", 1)[0]
    assert "respondWith" not in html_block


def test_bd_i18n_script_is_deferred():
    partial = Path("templates/partials/lang_switcher.html").read_text(encoding="utf-8")
    assert 'src="/static/js/bd_i18n.js" defer' in partial
