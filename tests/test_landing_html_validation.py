"""Landing page HTML validator guards (scoped body styles, a11y markup)."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def _landing_html() -> str:
    from dashboard import app

    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    return res.text


def test_body_style_blocks_use_scope():
    html = _landing_html()
    body = html.split("<body", 1)[-1]
    for match in re.finditer(r"<style[^>]*>(.*?)</style>", body, flags=re.I | re.S):
        assert "@scope" in match.group(1), "body <style> must wrap rules in @scope"


def test_landing_markup_validator_fixes():
    html = _landing_html()
    assert 'id="landingLang"' in html
    lang_snip = html[html.find("landingLang") : html.find("landingLang") + 120]
    assert "aria-label" not in lang_snip
    assert 'role="group"' in html and "landingStats" in html
    assert 'role="group"' in html and "bd-follow-row" in html
    assert 'role="contentinfo"' not in html
    assert 'id="shareCopyBtn"' in html
    assert 'href="#" href' not in html
    share_idx = html.find("shareCopyBtn")
    tag = html[share_idx - 80 : share_idx + 80]
    assert tag.count("href=") == 1
