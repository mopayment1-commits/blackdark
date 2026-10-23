"""Hard product rule: public website surfaces are English-only."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_HTML_ROOT_RE = re.compile(r"<html[^>]*>", re.IGNORECASE)

ARABIC_MARKERS = ("العرب", "مبتدئ", "احصل على", "قرار واحد", "التنبيه", "دقة Oracle", "جاري التحميل")


def _has_english_default_lang(text: str) -> bool:
    """Accept fixed lang=en or i18n template that defaults to English."""
    return (
        'lang="en"' in text
        or "lang='en'" in text
        or "lang|default('en')" in text
        or 'lang|default("en")' in text
    )


def test_primary_templates_are_english_html():
    templates = sorted((ROOT / "templates").glob("*.html"))
    assert templates, "expected HTML templates"
    for path in templates:
        text = path.read_text(encoding="utf-8")
        root_match = _HTML_ROOT_RE.search(text)
        assert root_match, path.name
        root_tag = root_match.group(0)
        assert _has_english_default_lang(root_tag), path.name
        if 'dir="rtl"' in root_tag:
            assert "dir|default" in root_tag, path.name
        for marker in ARABIC_MARKERS:
            assert marker not in text, f"{path.name} still contains Arabic UI marker: {marker}"


def test_oracle_default_lang_is_english():
    src = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert "resolved_api_lang" in src
    ux = (ROOT / "ux_mode.py").read_text(encoding="utf-8")
    assert 'lang: str = "en"' in ux
