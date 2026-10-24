#!/usr/bin/env python3
"""Translate specific catalog keys (or all EN-identical) into locales/*.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import ALLOW_IDENTICAL, EN, LOCALES, _effective_translation
from scripts.build_locale_json import TRANSLATE_TARGETS
from scripts.fill_locale_catalog_gaps import _translate_fast

LOCALES_DIR = ROOT / "locales"


def main() -> None:
    only_keys = [k.strip() for k in sys.argv[1:] if k.strip() and not k.startswith("--")]
    all_identical = "--all-identical" in sys.argv
    only_locales = [c.strip() for c in sys.argv[1:] if c.strip() in LOCALES]
    if "--all-identical" in sys.argv:
        only_locales = [c for c in sys.argv[2:] if c in LOCALES] or [
            c for c in LOCALES if c != "en"
        ]

    cache: dict[tuple[str, str], str] = {}
    for code in LOCALES:
        if code == "en":
            continue
        if only_locales and code not in only_locales:
            continue
        target = TRANSLATE_TARGETS.get(code)
        if not target:
            continue
        path = LOCALES_DIR / f"{code}.json"
        data = dict(EN)
        if path.is_file():
            data.update(json.loads(path.read_text(encoding="utf-8")))
        if only_keys:
            pending = [k for k in only_keys if k in EN]
        elif all_identical:
            pending = [
                k
                for k, en_val in EN.items()
                if k not in ALLOW_IDENTICAL
                and en_val.strip()
                and data.get(k, en_val) == en_val
            ]
        else:
            print("usage: translate_catalog_keys.py key1 key2 | --all-identical [locales…]")
            return
        if not pending:
            print(f"{code}: nothing to do")
            continue
        print(f"{code}: {len(pending)} keys", flush=True)
        for i, key in enumerate(pending):
            data[key] = _translate_fast(EN[key], target, cache)
            if (i + 1) % 100 == 0:
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (LOCALES_DIR / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("done", flush=True)


if __name__ == "__main__":
    main()
