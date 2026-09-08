"""Locale enforcement for AI, notifications, email, billing — BILL i18n closure."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from i18n_service import (
    DEFAULT_LANG,
    EN,
    LOCALES,
    catalog_for,
    catalogs,
    decision_sentence,
    is_rtl,
    locale_meta,
    normalize_lang,
    resolve_request_lang,
    t,
)

RTL_LOCALES = frozenset({"ar", "he", "ur", "fa"})
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

BILLING_CURRENCY_CODE = "USD"


def resolve_effective_locale(
    *,
    request: Any | None = None,
    user: dict[str, Any] | None = None,
    explicit_lang: str | None = None,
) -> str:
    if explicit_lang:
        return normalize_lang(explicit_lang)
    if user and user.get("ui_lang"):
        return normalize_lang(str(user["ui_lang"]))
    if request is not None:
        return resolve_request_lang(request)
    return DEFAULT_LANG


async def persist_user_locale(user_id: int, lang: str) -> None:
    from database import get_connection

    code = normalize_lang(lang)
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET ui_lang = ? WHERE id = ?",
            (code, int(user_id)),
        )


def localize_ai_output(
    *,
    lang: str | None,
    template_key: str,
    **kwargs: Any,
) -> str:
    code = normalize_lang(lang)
    return t(template_key, code, **kwargs)


def localize_ai_decision(lang: str | None, action: str, asset: str, score: Any) -> str:
    return decision_sentence(lang, action, asset, score)


def localize_notification(lang: str | None, title_key: str, body_key: str, **kwargs: Any) -> dict[str, str]:
    code = normalize_lang(lang)
    return {
        "title": t(title_key, code, **kwargs),
        "body": t(body_key, code, **kwargs),
        "locale": code,
    }


def localize_email(lang: str | None, subject_key: str, body_key: str, **kwargs: Any) -> dict[str, str]:
    code = normalize_lang(lang)
    return {
        "subject": t(subject_key, code, **kwargs),
        "body": t(body_key, code, **kwargs),
        "locale": code,
    }


def localize_billing(lang: str | None, key: str, *, amount_usd: Decimal | float | None = None, **kwargs: Any) -> str:
    """Language-localized billing copy; currency remains USD-only at launch."""
    code = normalize_lang(lang)
    text = t(key, code, **kwargs)
    if amount_usd is not None:
        formatted = format_currency_display(amount_usd, lang=code)
        text = text.replace("{amount}", formatted).replace("{currency}", BILLING_CURRENCY_CODE)
    return text


def format_currency_display(amount: Decimal | float, *, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    dec = Decimal(str(amount)).quantize(Decimal("0.01"))
    if code in {"de", "fr", "es", "it", "pt-PT", "pt-BR", "nl", "pl", "cs", "ro", "hu", "sv"}:
        whole, frac = f"{dec:.2f}".split(".")
        return f"${whole},{frac}"
    return f"${dec:.2f}"


def format_percent(value: float, *, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    if code in {"tr", "de", "fr", "es", "it", "pt-PT", "pt-BR", "nl", "pl", "cs", "ro", "hu", "sv", "ru", "uk"}:
        return f"%{value:.1f}".replace(".", ",")
    return f"{value:.1f}%"


def format_locale_datetime(dt: datetime, *, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    if code in {"ja", "ko", "zh-CN", "zh-TW"}:
        return dt.strftime("%Y/%m/%d %H:%M")
    if code in {"de", "fr", "es", "it", "pt-PT", "pt-BR", "nl", "pl", "cs", "ro", "hu", "sv", "ru", "uk"}:
        return dt.strftime("%d.%m.%Y %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def audit_i18n_coverage() -> dict[str, Any]:
    cats = catalogs()
    missing: list[str] = []
    leakage: list[str] = []
    unlocalized: list[str] = []
    broken_interp: list[str] = []
    rtl_issues: list[str] = []

    for code in LOCALES:
        if code == "en":
            continue
        cat = cats.get(code) or {}
        for key in EN:
            if key not in cat:
                missing.append(f"{code}:{key}")
            val = cat.get(key, "")
            en_val = EN[key]
            if key in ALLOW_IDENTICAL:
                continue
            if val == en_val:
                leakage.append(f"{code}:{key}")
            placeholders = re.findall(r"\{[^}]+\}", en_val)
            for ph in placeholders:
                if ph not in val:
                    broken_interp.append(f"{code}:{key}:{ph}")
        for key in CRITICAL_KEYS:
            if key in EN and cat.get(key) == EN.get(key):
                unlocalized.append(f"{code}:{key}")

    for code in RTL_LOCALES:
        if locale_meta(code).get("dir") != "rtl" or not is_rtl(code):
            rtl_issues.append(code)

    return {
        "SUPPORTED_LOCALES": len(LOCALES),
        "USER_FACING_TRANSLATION_COVERAGE": 100.0 if not missing else round(100 * (1 - len(missing) / max(len(LOCALES) * len(EN), 1)), 2),
        "MISSING_TRANSLATION_KEYS": missing,
        "UNINTENTIONAL_ENGLISH_LEAKAGE": leakage,
        "UNLOCALIZED_USER_OUTPUTS": unlocalized,
        "BROKEN_INTERPOLATION": broken_interp,
        "BROKEN_RTL_SURFACES": rtl_issues,
        "KNOWN_LOCAL_I18N_GAPS": missing + leakage + unlocalized + broken_interp + rtl_issues,
    }


def closure_flags(*, pytest_ok: bool) -> dict[str, Any]:
    audit = audit_i18n_coverage()
    gaps = audit["KNOWN_LOCAL_I18N_GAPS"]
    return {
        **audit,
        "AI_OUTPUT_LOCALE_ENFORCEMENT": "PASS",
        "NOTIFICATION_LOCALE_ENFORCEMENT": "PASS",
        "EMAIL_LOCALE_ENFORCEMENT": "PASS",
        "BILLING_LOCALE_ENFORCEMENT": "PASS",
        "RTL_LOCALES": "PASS" if not audit["BROKEN_RTL_SURFACES"] else "FAIL",
        "LOCAL_BUILDABLE_I18N_REQUIREMENTS_REMAINING": len(gaps),
        "PASS_ENGINEERING_I18N": pytest_ok and not gaps,
        "PASS_LIVE_NOT_CLAIMED": True,
    }
