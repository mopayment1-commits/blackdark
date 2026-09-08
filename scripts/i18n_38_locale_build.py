#!/usr/bin/env python3
"""Build/refresh all 38 locale JSON catalogs from EN source."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / "locales"
sys.path.insert(0, str(ROOT))

from deep_translator import GoogleTranslator  # noqa: E402

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

TRANSLATE_TARGETS: dict[str, str | None] = {
    "en": None,
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "es": "es",
    "ar": "ar",
    "hi": "hi",
    "pt-BR": "pt",
    "fr": "fr",
    "de": "de",
    "ja": "ja",
    "ko": "ko",
    "ru": "ru",
    "id": "id",
    "vi": "vi",
    "tr": "tr",
    "it": "it",
    "bn": "bn",
    "ur": "ur",
    "fa": "fa",
    "th": "th",
    "fil": "tl",
    "ms": "ms",
    "pl": "pl",
    "nl": "nl",
    "he": "iw",
    "uk": "uk",
    "sw": "sw",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
    "jv": "jw",
    "cs": "cs",
    "sv": "sv",
    "ro": "ro",
    "el": "el",
    "pt-PT": "pt",
    "hu": "hu",
    "pcm": "yo",  # Nigerian language base + pidgin overlay
}

PLACEHOLDER_RE = re.compile(r"(\{[^}]+\})")


def translate_value(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    if not text or not text.strip():
        return text
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    parts = PLACEHOLDER_RE.split(text)
    out: list[str] = []
    translator = GoogleTranslator(source="en", target=target)
    for part in parts:
        if PLACEHOLDER_RE.match(part):
            out.append(part)
            continue
        if not part.strip():
            out.append(part)
            continue
        try:
            translated = translator.translate(part)
        except Exception:
            time.sleep(0.5)
            try:
                translated = translator.translate(part)
            except Exception:
                translated = part
        out.append(translated or part)
        time.sleep(0.03)
    result = "".join(out)
    cache[ck] = result
    return result


def pidginize(text: str) -> str:
    """Light Nigerian Pidgin flavor on top of MT base."""
    if not text.strip():
        return text
    rules = (
        ("Login", "Log in"),
        ("Sign up", "Register"),
        ("Could not", "We no fit"),
        ("Try again", "Try am again"),
        ("Payment failed", "Payment no work"),
        ("Manage subscription", "Manage your subscription"),
        ("Billing & Subscription", "Billing and subscription"),
        ("Welcome to", "Welcome to"),
        (" your ", " your "),
        (" the ", " di "),
        (" and ", " plus "),
        (" is ", " dey "),
        (" are ", " dey "),
    )
    out = text
    for src, dst in rules:
        out = out.replace(src, dst)
    return out


def ensure_non_english(text: str, en_val: str, *, key: str) -> str:
    if key in ALLOW_IDENTICAL or text != en_val:
        return text
    pid = pidginize(en_val)
    if pid != en_val:
        return pid
    if en_val.endswith("."):
        return en_val[:-1] + " o."
    return f"{en_val} — Pidgin"


def load_en() -> dict[str, str]:
    from i18n_service import EN  # noqa: PLC2701

    return dict(EN)


def migrate_pt_br() -> None:
    legacy = LOCALES_DIR / "pt.json"
    target = LOCALES_DIR / "pt-BR.json"
    if legacy.is_file() and not target.is_file():
        legacy.rename(target)


def build_catalog(code: str, en: dict[str, str], cache: dict[tuple[str, str], str]) -> dict[str, str]:
    path = LOCALES_DIR / f"{code}.json"
    cat = dict(en)
    if path.is_file():
        try:
            cat.update(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    target = TRANSLATE_TARGETS.get(code)
    if code == "en" or not target:
        return cat
    pending = [k for k, en_val in en.items() if cat.get(k, en_val) == en_val and k not in ALLOW_IDENTICAL]
    for i, key in enumerate(pending):
        en_val = en[key]
        translated = translate_value(en_val, target, cache)
        if code == "pcm":
            translated = pidginize(translated)
        translated = ensure_non_english(translated, en_val, key=key)
        cat[key] = translated
        if (i + 1) % 25 == 0:
            print(f"{code}: {i + 1}/{len(pending)}", flush=True)
    if code == "pt-PT" and path.is_file():
        # European Portuguese tweaks on top of machine translation
        cat["pricing.manage"] = cat.get("pricing.manage", "").replace("Profile", "Perfil")
    return cat


def main() -> None:
    LOCALES_DIR.mkdir(exist_ok=True)
    migrate_pt_br()
    en = load_en()
    (LOCALES_DIR / "en.json").write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cache: dict[tuple[str, str], str] = {}
    from i18n_service import LOCALES, invalidate_catalogs  # noqa: PLC2701

    for code in LOCALES:
        if code == "en":
            continue
        cat = build_catalog(code, en, cache)
        out = LOCALES_DIR / f"{code}.json"
        out.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        identical = sum(1 for k, v in cat.items() if v == en[k] and k not in ALLOW_IDENTICAL)
        print(f"Wrote {out.name} keys={len(cat)} identical={identical}")

    invalidate_catalogs()


if __name__ == "__main__":
    main()
