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
    assert 'lang="ar"' in ar and 'dir="rtl"' in ar
    assert "We publish the miss." in en
    assert "ننشر الخطأ." in ar
    assert "We publish the miss." not in ar
    assert "تقسيم المميزات" in ar
    assert "تسجيل الدخول" in ar
    assert "إنشاء حساب" in ar
    assert 'id="lenses"' in ar


def test_french_changes_hero():
    fr = client.get("/?lang=fr").text
    assert "Nous publions l'échec." in fr
    assert 'lang="fr"' in fr


def test_login_arabic_tabs():
    ar = client.get("/login?lang=ar").text
    assert "إنشاء حساب" in ar
    assert "تسجيل" in ar or "دخول" in ar
