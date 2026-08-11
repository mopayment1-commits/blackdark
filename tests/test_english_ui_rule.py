"""Hard product rule: public website surfaces are English-only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
        assert _has_english_default_lang(text), path.name
        assert 'dir="rtl"' not in text, path.name
        for marker in ARABIC_MARKERS:
            assert marker not in text, f"{path.name} still contains Arabic UI marker: {marker}"


def test_oracle_default_lang_is_english():
    src = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert 'lang: str = "en"' in src
    ux = (ROOT / "ux_mode.py").read_text(encoding="utf-8")
    assert 'lang: str = "en"' in ux
