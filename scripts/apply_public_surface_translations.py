#!/usr/bin/env python3
"""Fill public-surface i18n keys in locales/*.json (machine translation)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import translators as ts

from i18n_service import (
    ALLOW_IDENTICAL,
    EN,
    LOCALES,
    _effective_translation,
    _hydrate_en_from_json_file,
    _load_json_catalog,
    locale_ui_complete,
    public_surface_keys,
)
from scripts.build_locale_json import TRANSLATE_TARGETS

_hydrate_en_from_json_file()

LOCALES_DIR = ROOT / "locales"


def _translate_ui(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    out = text
    for attempt in range(5):
        try:
            out = ts.translate_text(text[:4500], to_language=target, translator="bing")
            break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    out = (out or text).strip()
    if out.strip().lower() == text.strip().lower() and len(text.strip()) > 2:
        try:
            alt = ts.translate_text(f"UI label: {text}"[:4500], to_language=target, translator="bing")
            alt = (alt or "").replace("UI label:", "").replace("UI label", "").strip()
            if alt and alt.lower() != text.strip().lower():
                out = alt
        except Exception:
            pass
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
        loaded = _load_json_catalog(code) or {}
        data = dict(EN)
        data.update(loaded)
        pending = [
            k
            for k in keys
            if k in EN and k not in ALLOW_IDENTICAL and _effective_translation(code, k) is None
        ]
        if not pending:
            print(f"{code}: complete={locale_ui_complete(code)}", flush=True)
            continue
        print(f"{code}: {len(pending)} keys", flush=True)
        for i, key in enumerate(pending):
            en_val = EN[key]
            data[key] = _translate_ui(en_val, target, cache)
            time.sleep(0.28)
            if (i + 1) % 25 == 0:
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"  {i + 1}/{len(pending)}", flush=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # second pass for cognates still equal to English
        pending2 = [k for k in keys if k in EN and k not in ALLOW_IDENTICAL and _effective_translation(code, k) is None]
        if pending2:
            print(f"{code}: retry {len(pending2)}", flush=True)
            for key in pending2:
                data[key] = _translate_ui(f"{EN[key]} —", target, cache).rstrip("—- ").strip()
                time.sleep(0.28)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{code}: complete={locale_ui_complete(code)}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
