"""38-locale public UI i18n + enforcement + completeness."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")

REQUIRED_LOCALES = (
    "en",
    "zh-CN",
    "zh-TW",
    "es",
    "ar",
    "hi",
    "pt-BR",
    "fr",
    "de",
    "ja",
    "ko",
    "ru",
    "id",
    "vi",
    "tr",
    "it",
    "bn",
    "ur",
    "fa",
    "th",
    "fil",
    "ms",
    "pl",
    "nl",
    "he",
    "uk",
    "sw",
    "ta",
    "te",
    "mr",
    "jv",
    "cs",
    "sv",
    "ro",
    "el",
    "pt-PT",
    "hu",
    "pcm",
)

ADDED_LOCALES = (
    "uk",
    "sw",
    "ta",
    "te",
    "mr",
    "jv",
    "cs",
    "sv",
    "ro",
    "el",
    "pt-PT",
    "hu",
    "pcm",
)

RTL_LOCALES = ("ar", "he", "ur", "fa")

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
        "ui.oi",
        "ui.asset",
    }
)

CRITICAL_KEYS = (
    "nav.login",
    "nav.signup",
    "hero.headline",
    "hero.support",
    "lang.label",
    "login.tab.login",
    "oracle.get_decision",
    "pricing.title",
    "pulse.sentence",
    "billing.status.title",
    "notification.payment_failed.title",
    "email.billing_receipt.subject",
    "ai.summary.lead",
)


def test_supported_locale_count_is_38():
    from i18n_service import LOCALES

    assert len(LOCALES) == 38
    assert set(LOCALES.keys()) == set(REQUIRED_LOCALES)


def test_catalogs_cover_all_38_locales():
    from i18n_service import EN, LOCALES, catalogs, invalidate_catalogs, t

    invalidate_catalogs()
    cats = catalogs()
    assert set(cats) == set(REQUIRED_LOCALES)
    assert set(LOCALES.keys()) == set(REQUIRED_LOCALES)
    for code in REQUIRED_LOCALES:
        cat = cats[code]
        for key in EN:
            assert key in cat, f"{code} missing {key}"
        assert t("nav.login", code)
    assert t("nav.login", "ar") != t("nav.login", "en")
    assert "{asset}" in t("decision.act", "ja")


def test_non_en_locales_translate_critical_keys_all_38():
    from i18n_service import EN, catalog_for, invalidate_catalogs

    invalidate_catalogs()
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


def test_normalize_aliases_pt_split_and_pcm():
    from i18n_service import normalize_lang

    assert normalize_lang("zh") == "zh-CN"
    assert normalize_lang("zh-TW") == "zh-TW"
    assert normalize_lang("pt-BR") == "pt-BR"
    assert normalize_lang("pt") == "pt-BR"
    assert normalize_lang("pt-PT") == "pt-PT"
    assert normalize_lang("EN-us") == "en"
    assert normalize_lang("tl") == "fil"
    assert normalize_lang("iw") == "he"
    assert normalize_lang("fa-IR") == "fa"
    assert normalize_lang("pidgin") == "pcm"
    assert normalize_lang("uk") == "uk"


def test_ai_output_locale_enforcement_all_38():
    from i18n_enforcement import localize_ai_decision, localize_ai_output

    for code in REQUIRED_LOCALES:
        summary = localize_ai_output(lang=code, template_key="ai.summary.lead")
        assert summary
        if code != "en":
            assert summary != "Summary", f"{code} AI summary leaked English"
        decision = localize_ai_decision(code, "ACT", "BTC", 77)
        assert "BTC" in decision
        assert "77" in decision


def test_notification_locale_enforcement_all_38():
    from i18n_enforcement import localize_notification

    for code in REQUIRED_LOCALES:
        note = localize_notification(
            code,
            "notification.payment_failed.title",
            "notification.payment_failed.body",
        )
        assert note["locale"] == code
        assert note["title"]
        assert note["body"]
        if code != "en":
            assert note["title"] != "Payment failed", code


def test_email_locale_enforcement_all_38():
    from i18n_enforcement import localize_email

    for code in REQUIRED_LOCALES:
        mail = localize_email(
            code,
            "email.billing_receipt.subject",
            "email.billing_receipt.body",
            amount="$29.00",
        )
        assert mail["locale"] == code
        assert mail["subject"]
        assert mail["body"]
        if code != "en":
            assert mail["subject"] != "Your BLACKDARK receipt", code


def test_billing_locale_enforcement_all_38():
    from decimal import Decimal

    from i18n_enforcement import BILLING_CURRENCY_CODE, format_currency_display, localize_billing

    for code in REQUIRED_LOCALES:
        title = localize_billing(code, "billing.status.title")
        assert title
        if code != "en":
            assert title != "Billing & Subscription", code
        currency_note = localize_billing(code, "billing.currency.usd_only")
        if code == "en":
            assert "USD" in currency_note
        else:
            assert currency_note != "All prices shown in USD.", code
        formatted = format_currency_display(Decimal("29.00"), lang=code)
        assert formatted.startswith("$")


def test_audit_i18n_coverage_clean():
    from i18n_enforcement import audit_i18n_coverage
    from i18n_service import invalidate_catalogs

    invalidate_catalogs()
    audit = audit_i18n_coverage()
    assert audit["SUPPORTED_LOCALES"] == 38
    assert audit["USER_FACING_TRANSLATION_COVERAGE"] == 100.0
    assert audit["MISSING_TRANSLATION_KEYS"] == []
    assert audit["UNINTENTIONAL_ENGLISH_LEAKAGE"] == []
    assert audit["UNLOCALIZED_USER_OUTPUTS"] == []
    assert audit["BROKEN_RTL_SURFACES"] == []


@pytest.mark.asyncio
async def test_pages_and_api_switch_language_38():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        en = await client.get("/")
        assert en.status_code == 200
        assert 'lang="en"' in en.text

        ar = await client.get("/?lang=ar")
        assert ar.status_code == 200
        assert 'lang="ar"' in ar.text
        assert 'dir="rtl"' in ar.text

        uk = await client.get("/?lang=uk")
        assert uk.status_code == 200
        assert 'lang="uk"' in uk.text

        pcm = await client.get("/?lang=pcm")
        assert pcm.status_code == 200
        assert 'lang="pcm"' in pcm.text

        locales = await client.get("/api/i18n/locales")
        assert locales.status_code == 200
        body = locales.json()
        assert body["count"] == 38
        assert body["default"] == "en"
        assert set(body["rtl"]) == set(RTL_LOCALES)

        for code in ADDED_LOCALES:
            cat = await client.get(f"/api/i18n/catalog?lang={code}")
            assert cat.status_code == 200
            assert cat.json()["lang"] == code


@pytest.mark.asyncio
async def test_dispatch_alert_localized_notification():
    from alert_service import dispatch_alert

    result = await dispatch_alert(
        "",
        "",
        lang="fr",
        title_key="notification.oracle.title",
        body_key="notification.oracle.body",
        asset="ETH",
        channels=["in_app"],
    )
    assert result["locale"] == "fr"
    assert result["title"] != "Oracle alert"


def test_decision_sentence_localized():
    from i18n_service import decision_sentence

    en = decision_sentence("en", "ACT", "ETH", 80)
    ar = decision_sentence("ar", "ACT", "ETH", 80)
    ur = decision_sentence("ur", "ACT", "ETH", 80)
    pcm = decision_sentence("pcm", "ACT", "ETH", 80)
    assert "ETH" in en
    assert "80" in en
    assert en != ar
    assert ur != en
    assert pcm != en
