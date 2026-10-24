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

from i18n_service import (
    EN,
    LOCALES,
    _effective_translation,
    _load_json_catalog,
    public_surface_keys,
)
from scripts.build_locale_json import TRANSLATE_TARGETS
from scripts.fill_locale_catalog_gaps import _translate_fast as _translate

LOCALES_DIR = ROOT / "locales"


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
        data = dict(EN)
        data.update(_load_json_catalog(code) or {})
        pending = [k for k in keys if _effective_translation(code, k) is None]
        if not pending:
            print(f"{code}: complete", flush=True)
            continue
        print(f"{code}: {len(pending)} public keys", flush=True)
        for i, key in enumerate(pending):
            en_val = EN[key]
            if not en_val.strip():
                continue
            data[key] = _translate(en_val, target, cache)
            time.sleep(0.015)
            if (i + 1) % 40 == 0:
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                print(f"  {code}: {i + 1}/{len(pending)}", flush=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        still = [k for k in keys if _effective_translation(code, k) is None]
        print(f"{code}: wrote ({len(still)} still missing)", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
