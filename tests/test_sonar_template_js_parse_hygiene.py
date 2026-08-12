"""Regression: no Jinja/template tokens inside executable HTML <script> bodies.

Sonar JS parser fails on ``{{ ... }}`` inside JS (coin.html / lang_switcher.html).
Executable logic must live in ``static/js/*.js``; templates may only boot via
data-* attributes or ``application/json`` script blocks.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
STATIC_JS = ROOT / "static" / "js"

_JINJA_OPEN = re.compile(r"\{\{|\{%")


class _ScriptCollector(HTMLParser):
    """Collect executable script bodies (skip JSON / JSON-LD boots)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.scripts: list[str] = []
        self._capture = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        typ = attr_map.get("type", "").strip().lower()
        if typ in {"application/json", "application/ld+json"}:
            self._capture = False
            return
        # External src with empty body is fine; still capture any inline body.
        self._capture = True
        self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "script" or not self._capture:
            return
        self.scripts.append("".join(self._chunks))
        self._capture = False
        self._chunks = []


def _executable_script_bodies(html: str) -> list[str]:
    parser = _ScriptCollector()
    parser.feed(html)
    parser.close()
    return [body for body in parser.scripts if body.strip()]


def test_coin_detail_js_module_exists_and_is_plain_js():
    path = STATIC_JS / "coin_detail.js"
    assert path.is_file()
    src = path.read_text(encoding="utf-8")
    assert "plainText" in src
    assert "textContent" in src
    assert "stats.innerHTML" not in src
    assert "{{" not in src and "{%" not in src
    assert "getAttribute(\"data-coin-id\")" in src or "data-coin-id" in src


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
    for body in _executable_script_bodies(coin):
        assert not _JINJA_OPEN.search(body), body[:200]


def test_lang_switcher_boots_via_json_not_jinja_in_js():
    sw = (TEMPLATES / "partials/lang_switcher.html").read_text(encoding="utf-8")
    assert 'id="bd-i18n-boot"' in sw
    assert 'type="application/json"' in sw
    assert "/static/js/bd_i18n.js" in sw
    assert "window.BD_I18N = window.BD_I18N || {" not in sw
    for body in _executable_script_bodies(sw):
        assert not _JINJA_OPEN.search(body), body[:200]


def test_templates_executable_scripts_have_no_jinja_tokens():
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for body in _executable_script_bodies(text):
            if _JINJA_OPEN.search(body):
                offenders.append(str(path.relative_to(ROOT)))
                break
    assert offenders == [], f"Jinja inside executable <script>: {offenders}"
