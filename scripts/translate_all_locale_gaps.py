#!/usr/bin/env python3
"""Translate every locale key that still equals English (MyMemory HTTP)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES, _load_json_catalog
from scripts.build_locale_json import ALLOW_IDENTICAL
from scripts.fill_feature_i18n_keys import mm_translate, LANGPAIR


def main() -> int:
    only = [c.strip() for c in sys.argv[1:] if c.strip()]
    locales_dir = ROOT / "locales"
    cache: dict[tuple[str, str], str] = {}
    stats: dict[str, int] = {}

    (locales_dir / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for code in LOCALES:
        if code == "en":
            continue
        if only and code not in only:
            continue
        target = LANGPAIR.get(code)
        path = locales_dir / f"{code}.json"
        cat = dict(_load_json_catalog(code) or {})
        for k in EN:
            cat.setdefault(k, EN[k])
        pending = [
            k
            for k in EN
            if cat.get(k, EN[k]) == EN[k] and k not in ALLOW_IDENTICAL
        ]
        translated = 0
        if target and pending:
            print(f"{code}: {len(pending)} gaps", flush=True)
            for i, key in enumerate(pending):
                cat[key] = mm_translate(EN[key], target, cache)
                if cat[key] != EN[key]:
                    translated += 1
                if (i + 1) % 50 == 0:
                    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"  {code}: {i + 1}/{len(pending)}", flush=True)
                time.sleep(0.2)
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats[code] = translated
        print(f"wrote {code}: translated {translated} keys", flush=True)

    print("SUMMARY", json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
