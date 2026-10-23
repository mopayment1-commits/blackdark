#!/usr/bin/env python3
"""Translate keys required for locale_ui_complete() across all locales/*.json."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import (  # noqa: E402
    EN,
    LOCALES,
    _effective_translation,
    _hydrate_en_from_json_file,
    _load_json_catalog,
    locale_ui_complete,
    public_surface_keys,
)

_hydrate_en_from_json_file()
public_surface_keys.cache_clear()
from scripts.build_locale_json import ALLOW_IDENTICAL
from scripts.fill_feature_i18n_keys import LANGPAIR, mm_translate


def main() -> int:
    only = [c.strip() for c in sys.argv[1:] if c.strip()]
    locales_dir = ROOT / "locales"
    cache: dict[tuple[str, str], str] = {}
    (locales_dir / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ps = set(public_surface_keys())
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
            for k in ps
            if k in EN
            and k not in ALLOW_IDENTICAL
            and _effective_translation(code, k) is None
            and cat.get(k, EN[k]) == EN[k]
        ]
        translated = 0
        if target and pending:
            print(f"{code}: {len(pending)} public-surface gaps", flush=True)
            for i, key in enumerate(pending):
                cat[key] = mm_translate(EN[key], target, cache)
                if cat[key] != EN[key]:
                    translated += 1
                if (i + 1) % 40 == 0:
                    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                time.sleep(0.18)
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ok = locale_ui_complete(code)
        print(f"wrote {code}: translated {translated}, complete={ok}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
