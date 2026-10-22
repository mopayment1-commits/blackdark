"""WebAIM-oriented landing accessibility guards."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def _landing_html() -> str:
    from dashboard import app

    res = TestClient(app).get("/")
    assert res.status_code == 200
    return res.text


def test_unique_follow_heading_ids():
    html = _landing_html()
    assert html.count('id="follow-us-heading"') == 1
    assert 'id="footer-follow-heading"' in html


def test_follow_section_aria_reference():
    html = _landing_html()
    assert 'aria-labelledby="follow-us-heading"' in html
    assert html.index('aria-labelledby="follow-us-heading"') < html.index('id="follow-us-heading"')


def test_ask_ai_and_watchlist_have_labels():
    html = _landing_html()
    assert 'for="bdAskAiInput"' in html
    assert 'for="bdWatchlistInput"' in html


def test_seal_steps_use_headings_not_strong():
    html = _landing_html()
    assert 'class="seal-step-title"' in html
    assert re.search(r'<div class="seal-step">\s*<strong>', html) is None


def test_landing_body_class_for_contrast():
    html = _landing_html()
    assert 'class="landing-page"' in html or 'landing-page' in html.split("<body", 1)[1][:80]
