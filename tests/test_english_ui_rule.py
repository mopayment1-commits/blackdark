"""Hard product rule: public website surfaces are English-only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ARABIC_MARKERS = ("العرب", "مبتدئ", "احصل على", "قرار واحد", "التنبيه", "دقة Oracle", "جاري التحميل")


def test_primary_templates_are_english_html():
    for rel in (
        "templates/landing.html",
        "templates/dashboard.html",
        "templates/oracle_accuracy.html",
        "templates/admin_launch.html",
        "templates/index.html",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert 'lang="en"' in text or "lang='en'" in text or "<html lang=\"en\"" in text or 'lang="en"' in text[:200] or "lang=\"en\"" in text
        assert "dir=\"rtl\"" not in text
        for marker in ARABIC_MARKERS:
            assert marker not in text, f"{rel} still contains Arabic UI marker: {marker}"


def test_oracle_default_lang_is_english():
    src = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert 'lang: str = "en"' in src
    ux = (ROOT / "ux_mode.py").read_text(encoding="utf-8")
    assert 'lang: str = "en"' in ux
