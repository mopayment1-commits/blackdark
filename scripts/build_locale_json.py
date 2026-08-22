#!/usr/bin/env python3
"""Build complete locale JSON catalogs from EN source + overlays + machine translation."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = ROOT / "locales"

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRANSLATE_TARGETS: dict[str, str | None] = {
    "en": None,
    "es": "es",
    "ar": "ar",
    "pt": "pt",
    "fr": "fr",
    "de": "de",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "hi": "hi",
    "tr": "tr",
    "ru": "ru",
    "id": "id",
    "vi": "vi",
    "th": "th",
    "fil": "tl",
    "it": "it",
    "bn": "bn",
    "ur": "ur",
    "fa": "fa",
    "ms": "ms",
    "pl": "pl",
    "nl": "nl",
    "he": "iw",
}

# Keys that may legitimately match English (brand, tier SKUs, placeholders-only).
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

PLACEHOLDER_RE = re.compile(r"(\{[^}]+\})")

# Only protect format placeholders — product names pass through to the translator.
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
            time.sleep(0.35)
            try:
                translated = translator.translate(part)
            except Exception:
                translated = part
        out.append(translated or part)
        time.sleep(0.04)
    result = "".join(out)
    cache[ck] = result
    return result


def seed_catalogs() -> dict[str, dict[str, str]]:
    from i18n_service import EN, _TRANSLATIONS  # noqa: PLC2701
    from i18n_locales import LOCALE_OVERLAYS  # noqa: PLC2701

    catalogs: dict[str, dict[str, str]] = {"en": dict(EN)}
    merged: dict[str, dict[str, str]] = {}
    for code, overlay in LOCALE_OVERLAYS.items():
        merged.setdefault(code, {})
        merged[code].update(overlay)
    for code, overlay in _TRANSLATIONS.items():
        merged.setdefault(code, {})
        merged[code].update(overlay)

    for code in TRANSLATE_TARGETS:
        if code == "en":
            continue
        cat = dict(EN)
        cat.update(merged.get(code, {}))
        catalogs[code] = cat
    return catalogs


def main() -> None:
    LOCALES_DIR.mkdir(exist_ok=True)
    catalogs = seed_catalogs()
    cache: dict[tuple[str, str], str] = {}

    for code, target in TRANSLATE_TARGETS.items():
        cat = catalogs[code]
        if code != "en" and target:
            pending = [k for k, en_val in catalogs["en"].items() if cat.get(k, en_val) == en_val and k not in ALLOW_IDENTICAL]
            for i, key in enumerate(pending):
                en_val = catalogs["en"][key]
                cat[key] = translate_value(en_val, target, cache)
                if (i + 1) % 20 == 0:
                    print(f"{code}: {i + 1}/{len(pending)} keys…", flush=True)
        out_path = LOCALES_DIR / f"{code}.json"
        out_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        identical = sum(1 for k, v in cat.items() if v == catalogs["en"][k] and k not in ALLOW_IDENTICAL)
        print(f"Wrote {out_path.name} ({len(cat)} keys, {identical} identical-to-en outside allowlist)")


if __name__ == "__main__":
    main()
