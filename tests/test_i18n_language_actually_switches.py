"""Selecting a language must change visible landing copy (not only html lang/dir)."""

from __future__ import annotations

import os

os.environ.setdefault("SOFT_LAUNCH", "1")

from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)


def test_arabic_changes_hero_and_lenses_and_nav():
    en = client.get("/").text
    ar = client.get("/?lang=ar").text
    assert 'lang="ar"' in ar
    assert 'dir="rtl"' in ar
    assert "We publish the miss." in en
    assert "ننشر الخطأ." in ar
    # Body headline must not stay English (meta may still mention brand EN in rare cases)
    assert 'class="hero-headline">ننشر الخطأ.</p>' in ar or ">ننشر الخطأ.</p>" in ar
    assert 'class="hero-headline">We publish the miss.</p>' not in ar
    assert "تقسيم المميزات" not in ar
    assert "تسجيل الدخول" in ar
    assert "إنشاء حساب" in ar
    assert 'href="/lenses"' in ar


def test_french_changes_hero():
    fr = client.get("/?lang=fr").text
    # Apostrophe may be HTML-escaped in attributes/body depending on Jinja autoescape.
    assert ("Nous publions l'échec." in fr) or ("Nous publions l&#39;échec." in fr)
    assert 'lang="fr"' in fr


def test_login_arabic_tabs():
    ar = client.get("/login?lang=ar").text
    assert "إنشاء حساب" in ar
    assert "دخول" in ar


def test_oracle_accuracy_french_glass_box():
    fr = client.get("/oracle-accuracy?lang=fr").text
    assert 'lang="fr"' in fr
    assert "The Glass Box Challenge" not in fr
    assert "Défi" in fr or "boîte" in fr.lower() or "transparence" in fr.lower()


def test_core_locales_public_surface_complete():
    from i18n_service import locale_ui_complete

    for code in ("ar", "es", "ja", "fr"):
        assert locale_ui_complete(code), f"{code} missing public-surface translations"
