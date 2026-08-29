"""Expanded WCAG accessibility tests — static + template coverage."""

from __future__ import annotations

from pathlib import Path

from accessibility_audit_service import run_static_wcag_audit


def test_static_wcag_audit_all_templates_pass():
    audit = run_static_wcag_audit()
    assert audit["ok"] is True, audit["scans"][:5]
    assert audit["templates_failing"] == 0


def test_landing_hero_has_non_empty_alt():
    html = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'class="hero-bleed-img"' in html
    assert 'alt=""' not in html.split("hero-bleed-img")[1].split(">")[0]
    assert "alt=" in html


def test_data_lineage_page_has_lang_en():
    html = Path("templates/data_lineage.html").read_text(encoding="utf-8")
    assert "lang|default('en')" in html or 'lang|default("en")' in html or 'lang="en"' in html
