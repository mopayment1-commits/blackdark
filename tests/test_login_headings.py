"""Login page — single h1 and document title length."""

from __future__ import annotations


def test_login_page_single_h1_and_title():
    from i18n_service import EN

    title = EN["meta.title.login"]
    assert 40 <= len(title) <= 60

    from pathlib import Path

    html = Path(__file__).resolve().parents[1] / "templates" / "login.html"
    text = html.read_text(encoding="utf-8")
    assert text.count("<h1") == 1
    assert "auth-subheading" in text
    assert "meta.title.login" in text
