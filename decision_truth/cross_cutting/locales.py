"""Canonical 38-locale coverage target for DTS presentation."""

from __future__ import annotations

from failure.error_i18n_static import ERROR_I18N_OVERLAYS

# 37 error locales + English source = 38 canonical coverage target.
CANONICAL_38_LOCALES: tuple[str, ...] = tuple(sorted(set(ERROR_I18N_OVERLAYS.keys()) | {"en"}))

_LOCALE_ALIASES: dict[str, str] = {
    "pt-br": "pt",
    "pt_br": "pt",
    "pt-pt": "pt",
    "pt_pt": "pt",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh_tw": "zh-TW",
    "iw": "he",
    "fil-ph": "fil",
    "tl": "fil",
}


def normalize_dts_locale(lang: str | None) -> str:
    raw = (lang or "en").strip().replace("_", "-")
    if not raw:
        return "en"
    lower = raw.lower()
    if lower in _LOCALE_ALIASES:
        mapped = _LOCALE_ALIASES[lower]
        return mapped if mapped in CANONICAL_38_LOCALES else "en"
    for code in CANONICAL_38_LOCALES:
        if code.lower() == lower:
            return code
    primary = lower.split("-", 1)[0]
    if primary in _LOCALE_ALIASES:
        mapped = _LOCALE_ALIASES[primary]
        return mapped if mapped in CANONICAL_38_LOCALES else "en"
    for code in CANONICAL_38_LOCALES:
        if code.lower() == primary or code.lower().startswith(primary + "-"):
            return code
    return "en"
