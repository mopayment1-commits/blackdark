"""Public UI: English is default; 15 locales available via language switcher."""

from __future__ import annotations

from pathlib import Path

from i18n_service import DEFAULT_LANG, LOCALES, normalize_lang


TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def test_default_lang_is_english():
    assert DEFAULT_LANG == "en"
    assert normalize_lang(None) == "en"
    assert normalize_lang("xx-YY") == "en"


def test_fifteen_locales_registered():
    assert len(LOCALES) == 15
    for code in (
        "en",
        "zh-CN",
        "hi",
        "ja",
        "ko",
        "ru",
        "pt",
        "es",
        "fr",
        "de",
        "ar",
        "tr",
        "vi",
        "id",
        "th",
    ):
        assert code in LOCALES
    assert LOCALES["ar"]["dir"] == "rtl"


def test_public_templates_use_lang_binding():
    """Core public shells bind html lang/dir from i18n context (not hard-locked en)."""
    for name in ("landing.html", "dashboard.html", "login.html", "oracle_accuracy.html"):
        text = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "lang=" in text
        assert "lang_switcher" in text or "bdLangSelect" in text or "partials/lang_switcher" in text, name
