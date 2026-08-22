"""25-locale public UI i18n + language switcher + completeness."""

from __future__ import annotations

import pytest

REQUIRED_LOCALES = (
    "en",
    "es",
    "ar",
    "pt",
    "fr",
    "de",
    "zh-CN",
    "zh-TW",
    "ja",
    "ko",
    "hi",
    "tr",
    "ru",
    "id",
    "vi",
    "th",
    "fil",
    "it",
    "bn",
    "ur",
    "fa",
    "ms",
    "pl",
    "nl",
    "he",
)

RTL_LOCALES = ("ar", "he", "ur", "fa")

# Keys that may match English (brand SKUs, tier names, universal acronyms).
ALLOW_IDENTICAL = frozenset(
    {
        "brand",
        "action.ACT",
        "action.WAIT",
        "pricing.pro",
        "pricing.whale",
        "pricing.decision_pro",
        "pricing.decision_desk",
        "stats.telegram",
        "oracle.mode.pro",
        "oracle.audience.pro",
        "oracle.audience.whale",
        "oracle.audience.fund",
        "oracle.audience.retail",
    }
)

CRITICAL_KEYS = (
    "nav.login",
    "nav.signup",
    "hero.headline",
    "hero.support",
    "lang.label",
    "login.tab.login",
    "login.tab.register",
    "oracle.get_decision",
    "accuracy.title",
    "pricing.title",
    "pulse.sentence",
)


def test_catalogs_cover_all_locales():
    from i18n_service import EN, LOCALES, catalogs, t

    cats = catalogs()
    assert set(LOCALES.keys()) == set(REQUIRED_LOCALES)
    assert set(cats) == set(REQUIRED_LOCALES)
    for code, cat in cats.items():
        for key in EN:
            assert key in cat, f"{code} missing {key}"
        assert t("nav.login", code)
    assert t("nav.login", "ar") != t("nav.login", "en")
    assert "{asset}" in t("decision.act", "ja")


def test_non_en_locales_translate_critical_keys():
    from i18n_service import EN, catalog_for

    for code in REQUIRED_LOCALES:
        if code == "en":
            continue
        cat = catalog_for(code)
        for key in CRITICAL_KEYS:
            en_val = EN[key]
            cur = cat[key]
            if key in ALLOW_IDENTICAL:
                continue
            assert cur != en_val, f"{code}.{key} still English: {cur!r}"


def test_rtl_locales():
    from i18n_service import is_rtl, locale_meta

    for code in RTL_LOCALES:
        assert is_rtl(code)
        assert locale_meta(code)["dir"] == "rtl"
    assert not is_rtl("en")
    assert not is_rtl("fr")


def test_normalize_aliases():
    from i18n_service import normalize_lang

    assert normalize_lang("zh") == "zh-CN"
    assert normalize_lang("zh-TW") == "zh-TW"
    assert normalize_lang("pt-BR") == "pt"
    assert normalize_lang("EN-us") == "en"
    assert normalize_lang("tl") == "fil"
    assert normalize_lang("iw") == "he"
    assert normalize_lang("fa-IR") == "fa"


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

        he = await client.get("/?lang=he")
        assert he.status_code == 200
        assert 'lang="he"' in he.text
        assert 'dir="rtl"' in he.text

        ja = await client.get("/dashboard?lang=ja")
        assert ja.status_code == 200
        assert 'lang="ja"' in ja.text
        assert "ログイン" in ja.text or "日本語" in ja.text

        locales = await client.get("/api/i18n/locales")
        assert locales.status_code == 200
        body = locales.json()
        assert body["count"] == 25
        assert body["default"] == "en"
        assert set(body["rtl"]) == set(RTL_LOCALES)

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
    ur = decision_sentence("ur", "ACT", "ETH", 80)
    assert "ETH" in en
    assert "80" in en
    assert "ETH" in ar
    assert "80" in ar
    assert en != ar
    assert ur != en
