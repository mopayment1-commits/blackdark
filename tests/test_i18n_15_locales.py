"""15-locale public UI i18n + language switcher."""

from __future__ import annotations

import pytest


def test_catalogs_cover_all_locales():
    from i18n_service import EN, LOCALES, catalogs, t

    cats = catalogs()
    assert set(cats) == set(LOCALES)
    for code, cat in cats.items():
        for key in EN:
            assert key in cat, f"{code} missing {key}"
        assert t("nav.login", code)
    assert t("nav.login", "ar") != t("nav.login", "en")
    assert "{asset}" in t("decision.act", "ja")


def test_normalize_aliases():
    from i18n_service import normalize_lang

    assert normalize_lang("zh") == "zh-CN"
    assert normalize_lang("pt-BR") == "pt"
    assert normalize_lang("EN-us") == "en"


@pytest.mark.asyncio
async def test_pages_and_api_switch_language():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        en = await client.get("/")
        assert en.status_code == 200
        assert 'lang="en"' in en.text
        assert "bdLangSelect" in en.text

        ar = await client.get("/?lang=ar")
        assert ar.status_code == 200
        assert 'lang="ar"' in ar.text
        assert 'dir="rtl"' in ar.text
        assert "تسجيل الدخول" in ar.text or "العربية" in ar.text

        ja = await client.get("/dashboard?lang=ja")
        assert ja.status_code == 200
        assert 'lang="ja"' in ja.text
        assert "ログイン" in ja.text or "日本語" in ja.text

        locales = await client.get("/api/i18n/locales")
        assert locales.status_code == 200
        body = locales.json()
        assert body["count"] == 15
        assert body["default"] == "en"

        cat = await client.get("/api/i18n/catalog?lang=es")
        assert cat.status_code == 200
        assert cat.json()["lang"] == "es"
        assert "nav.login" in cat.json()["catalog"]

        quick = await client.get("/oracle/BTC/quick?lang=fr")
        assert quick.status_code == 200
        data = quick.json()
        assert data.get("lang") == "fr"
        assert data.get("decision_sentence")


def test_decision_sentence_localized():
    from i18n_service import decision_sentence

    en = decision_sentence("en", "ACT", "ETH", 80)
    ar = decision_sentence("ar", "ACT", "ETH", 80)
    assert "ETH" in en
    assert "80" in en
    assert "ETH" in ar
    assert "80" in ar
    assert en != ar
