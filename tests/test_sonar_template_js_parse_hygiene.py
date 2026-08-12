"""Regression: no Jinja/template tokens inside executable HTML <script> bodies.

Sonar JS parser fails on ``{{ ... }}`` inside JS (coin.html / lang_switcher.html).
Executable logic must live in ``static/js/*.js``; templates may only boot via
data-* attributes or ``application/json`` script blocks.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
STATIC_JS = ROOT / "static" / "js"

# Match classic JS script bodies (exclude JSON-LD / application/json boots).
_SCRIPT_RE = re.compile(
    r"<script(?![^>]*\btype\s*=\s*[\"']application/(?:json|ld\+json)[\"'])[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_JINJA_IN_JS = re.compile(r"\{\{|\{%")


def test_coin_detail_js_module_exists_and_is_plain_js():
    path = STATIC_JS / "coin_detail.js"
    assert path.is_file()
    src = path.read_text(encoding="utf-8")
    assert "plainText" in src
    assert "textContent" in src
    assert "stats.innerHTML" not in src
    assert "{{" not in src and "{%" not in src
    assert "data-coin-id" in src or "getAttribute(\"data-coin-id\")" in src


def test_bd_i18n_js_module_exists_and_is_plain_js():
    path = STATIC_JS / "bd_i18n.js"
    assert path.is_file()
    src = path.read_text(encoding="utf-8")
    assert "BD_I18N" in src
    assert "bd-i18n-boot" in src
    assert "setLang" in src
    assert "{{" not in src and "{%" not in src


def test_coin_html_has_no_executable_inline_js_with_jinja():
    coin = (TEMPLATES / "coin.html").read_text(encoding="utf-8")
    assert 'id="coinPage"' in coin
    assert "data-coin-id=" in coin
    assert "/static/js/coin_detail.js" in coin
    assert "plainText" not in coin  # logic moved to static module
    for body in _SCRIPT_RE.findall(coin):
        if not body.strip():
            continue
        # External src scripts have empty bodies; inline must not contain Jinja.
        assert not _JINJA_IN_JS.search(body), body[:200]


def test_lang_switcher_boots_via_json_not_jinja_in_js():
    sw = (TEMPLATES / "partials/lang_switcher.html").read_text(encoding="utf-8")
    assert 'id="bd-i18n-boot"' in sw
    assert 'type="application/json"' in sw
    assert "/static/js/bd_i18n.js" in sw
    assert "window.BD_I18N = window.BD_I18N || {" not in sw
    for body in _SCRIPT_RE.findall(sw):
        if not body.strip():
            continue
        assert not _JINJA_IN_JS.search(body), body[:200]


def test_templates_executable_scripts_have_no_jinja_tokens():
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for body in _SCRIPT_RE.findall(text):
            if not body.strip():
                continue
            if _JINJA_IN_JS.search(body):
                offenders.append(str(path.relative_to(ROOT)))
                break
    assert offenders == [], f"Jinja inside executable <script>: {offenders}"
