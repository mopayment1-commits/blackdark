#!/usr/bin/env python3
"""Fix short public-surface labels that machine translation leaves identical to English."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import (
    ALLOW_IDENTICAL,
    EN,
    LOCALES,
    _effective_translation,
    public_surface_keys,
)
from scripts.build_locale_json import TRANSLATE_TARGETS
from scripts.fill_locale_catalog_gaps import _translate_fast

LOCALES_DIR = ROOT / "locales"

STUB_KEYS = (
    "bounty.log.col.ref",
    "bounty.log.col.status",
    "dash.alerts.target",
    "dash.symbol",
    "ledger.regime.col.regime",
    "ledger.regime.col.status",
    "pricing.public.institution_title",
    "profile.avatar_alt",
    "profile.section.plan",
)


def main() -> None:
    public_surface_keys.cache_clear()
    keys = set(public_surface_keys())
    cache: dict[tuple[str, str], str] = {}
    for code in LOCALES:
        if code == "en":
            continue
        target = TRANSLATE_TARGETS.get(code)
        if not target:
            continue
        path = LOCALES_DIR / f"{code}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        merged = dict(EN)
        merged.update(data)
        touched = False
        for key in STUB_KEYS:
            if key not in keys or key in ALLOW_IDENTICAL:
                continue
            if _effective_translation(code, key) is not None:
                continue
            en_val = EN[key]
            merged[key] = _translate_fast(en_val, target, cache)
            touched = True
        if touched:
            path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{code}: patched cognate stubs", flush=True)


if __name__ == "__main__":
    main()
