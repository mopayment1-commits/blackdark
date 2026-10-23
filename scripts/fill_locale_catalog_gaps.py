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

from i18n_service import EN, LOCALES, _load_json_catalog
from scripts.build_locale_json import ALLOW_IDENTICAL, TRANSLATE_TARGETS

LOCALES_DIR = ROOT / "locales"


def _translate(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    out = text
    for attempt in range(6):
        try:
            out = ts.translate_text(text, to_language=target, translator="bing")
            break
        except Exception:
            time.sleep(1.2 * (attempt + 1))
    cache[ck] = out or text
    return cache[ck]


def fill_locale(code: str, cache: dict[tuple[str, str], str]) -> int:
    target = TRANSLATE_TARGETS.get(code)
    if not target or code == "en":
        return 0
    path = LOCALES_DIR / f"{code}.json"
    data = dict(_load_json_catalog(code) or {})
    for k in EN:
        if k not in data:
            data[k] = EN[k]
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
        time.sleep(0.12)
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
