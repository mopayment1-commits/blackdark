"""WCAG-oriented accessibility checks."""

from __future__ import annotations

from pathlib import Path


def test_landing_hero_has_non_empty_alt():
    html = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'class="hero-bleed-img"' in html
    assert 'alt=""' not in html.split("hero-bleed-img")[1].split(">")[0]
    assert "alt=" in html


def test_data_lineage_page_template_exists():
    assert Path("templates/data_lineage.html").exists()
