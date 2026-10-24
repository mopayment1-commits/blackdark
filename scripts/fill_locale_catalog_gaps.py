#!/usr/bin/env python3
"""Machine-translate locale JSON keys that still equal English (full catalog)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import translators as ts
from deep_translator import GoogleTranslator

from i18n_service import ALLOW_IDENTICAL, EN, LOCALES, _load_json_catalog
from scripts.build_locale_json import TRANSLATE_TARGETS, translate_value

LOCALES_DIR = ROOT / "locales"


def _translate_fast(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    """Public-surface batch path — Bing first (Google often noop in CI/agents)."""
    if not text or not text.strip():
        return text
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    out = text
    for attempt in range(3):
        try:
            alt = ts.translate_text(text, to_language=target, translator="bing")
            if alt and alt.strip():
                out = alt.strip()
                break
        except Exception:
            time.sleep(0.4 * (attempt + 1))
    if out == text:
        out = translate_value(text, target, cache)
    cache[ck] = out or text
    return cache[ck]


def _translate(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    if not text or not text.strip():
        return text
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    out = translate_value(text, target, cache)
    if out == text and len(text.strip()) > 2:
        for attempt in range(5):
            try:
                alt = ts.translate_text(text, to_language=target, translator="bing")
                if alt and alt != text:
                    out = alt
                    break
            except Exception:
                time.sleep(0.8 * (attempt + 1))
        if out == text:
            try:
                alt = GoogleTranslator(source="en", target=target).translate(text)
                if alt and alt.strip():
                    out = alt
            except Exception:
                pass
    if out == text and len(text.strip()) > 1 and target not in ("en", "en-US"):
        try:
            forced = GoogleTranslator(source="auto", target=target).translate(f"UI label: {text}")
            if forced and forced.strip():
                cleaned = forced.strip()
                for prefix in ("UI label:", "UI Label:", "Etiqueta UI:", "UI-Label:"):
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix) :].strip()
                if cleaned and cleaned != text:
                    out = cleaned
        except Exception:
            pass
    cache[ck] = out or text
    return cache[ck]


def fill_locale(code: str, cache: dict[tuple[str, str], str]) -> int:
    target = TRANSLATE_TARGETS.get(code)
    if not target or code == "en":
        return 0
    path = LOCALES_DIR / f"{code}.json"
    data = dict(EN)
    data.update(_load_json_catalog(code) or {})
    pending = [
        k
        for k, en_val in EN.items()
        if data.get(k, en_val) == en_val and k not in ALLOW_IDENTICAL and en_val.strip()
    ]
    if not pending:
        return 0
    print(f"{code}: translating {len(pending)} keys…", flush=True)
    for i, key in enumerate(pending):
        data[key] = _translate(EN[key], target, cache)
        time.sleep(0.06)
        if (i + 1) % 100 == 0:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if (i + 1) % 50 == 0:
            print(f"  {code}: {i + 1}/{len(pending)}", flush=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(pending)


def main() -> None:
    only = [c.strip() for c in sys.argv[1:] if c.strip()]
    cache: dict[tuple[str, str], str] = {}
    codes = [c for c in LOCALES if c != "en"]
    if only:
        codes = [c for c in codes if c in only]
    total = 0
    for code in codes:
        total += fill_locale(code, cache)
    LOCALES_DIR.mkdir(exist_ok=True)
    (LOCALES_DIR / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"done — {total} keys translated across {len(codes)} locales")


if __name__ == "__main__":
    main()
