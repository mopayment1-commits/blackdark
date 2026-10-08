#!/usr/bin/env python3
"""Fill public-surface i18n keys in locales/*.json (rate-limited machine translation)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deep_translator import GoogleTranslator

from i18n_service import (
    ALLOW_IDENTICAL,
    EN,
    LOCALES,
    _effective_translation,
    _load_json_catalog,
    public_surface_keys,
)
from scripts.build_locale_json import TRANSLATE_TARGETS

LOCALES_DIR = ROOT / "locales"


def _translate_ui(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    prompt = f"UI copy ({target}): {text}"
    try:
        out = GoogleTranslator(source="en", target=target).translate(prompt)
    except Exception:
        time.sleep(2.0)
        out = GoogleTranslator(source="en", target=target).translate(prompt)
    if out.startswith("UI copy"):
        out = out.split(":", 1)[-1].strip()
    cache[ck] = out or text
    return cache[ck]


def main() -> None:
    public_surface_keys.cache_clear()
    keys = public_surface_keys()
    cache: dict[tuple[str, str], str] = {}
    only = [c.strip() for c in sys.argv[1:] if c.strip()]

    for code in LOCALES:
        if code == "en":
            continue
        if only and code not in only:
            continue
        target = TRANSLATE_TARGETS.get(code)
        if not target:
            continue
        path = LOCALES_DIR / f"{code}.json"
        data = _load_json_catalog(code) or {}
        pending = [k for k in keys if _effective_translation(code, k) is None]
        if not pending:
            print(f"{code}: complete")
            continue
        print(f"{code}: {len(pending)} keys", flush=True)
        for i, key in enumerate(pending):
            en_val = EN[key]
            data[key] = _translate_ui(en_val, target, cache)
            time.sleep(1.1)
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(pending)}", flush=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
