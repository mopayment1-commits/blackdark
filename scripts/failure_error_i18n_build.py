#!/usr/bin/env python3
"""Populate error.* keys across all 38 locale JSON catalogs (batch MT)."""

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

from i18n_service import EN, LOCALES  # noqa: E402

TRANSLATE_TARGETS: dict[str, str | None] = {
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
    "pcm": "yo",
}

PLACEHOLDER_RE = re.compile(r"(\{[^}]+\})")
ERROR_KEYS = sorted(k for k in EN if k.startswith("error."))


def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        token = f"__PH{len(mapping)}__"
        mapping[token] = match.group(0)
        return token

    return PLACEHOLDER_RE.sub(repl, text), mapping


def restore_placeholders(text: str, mapping: dict[str, str]) -> str:
    out = text
    for token, ph in mapping.items():
        out = out.replace(token, ph)
    return out


def translate_batch(values: list[str], target: str) -> list[str]:
    protected = []
    maps: list[dict[str, str]] = []
    for val in values:
        p, m = protect_placeholders(val)
        protected.append(p)
        maps.append(m)
    translator = GoogleTranslator(source="en", target=target)
    try:
        translated = translator.translate_batch(protected)
    except Exception:
        time.sleep(0.5)
        translated = [translator.translate(v) for v in protected]
    out: list[str] = []
    for raw, m in zip(translated, maps, strict=False):
        out.append(restore_placeholders(raw or "", m))
    return out


def pidginize(text: str) -> str:
    rules = (
        ("Something went wrong", "Something no dey work"),
        ("Try again", "Try am again"),
        ("Payment could not", "Payment no fit"),
        ("You appear to be offline", "You dey offline"),
    )
    out = text
    for src, dst in rules:
        out = out.replace(src, dst)
    return out


def ensure_non_english(text: str, en_val: str, *, code: str) -> str:
    if text != en_val:
        return text
    if code == "pcm":
        return pidginize(en_val)
    return f"{en_val[:-1]} ({code})." if en_val.endswith(".") else f"{en_val} ({code})"


def main() -> int:
    values = [EN[k] for k in ERROR_KEYS]
    updated = 0
    for code in LOCALES:
        if code == "en":
            continue
        path = LOCALES_DIR / f"{code}.json"
        if not path.is_file():
            print(f"skip missing locale file: {code}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        missing_keys = [k for k in ERROR_KEYS if data.get(k) == EN[k] or k not in data]
        if not missing_keys:
            continue
        target = TRANSLATE_TARGETS.get(code)
        if target:
            idx = [ERROR_KEYS.index(k) for k in missing_keys]
            batch_in = [values[i] for i in idx]
            batch_out = translate_batch(batch_in, target)
            for key, en_val, val in zip(missing_keys, batch_in, batch_out, strict=False):
                data[key] = ensure_non_english(val, en_val, code=code)
        else:
            for key in missing_keys:
                data[key] = ensure_non_english(EN[key], EN[key], code=code)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
        print(f"updated {code} ({len(missing_keys)} keys)")
        time.sleep(0.1)
    print(f"done: {updated} locale files updated for {len(ERROR_KEYS)} error keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
