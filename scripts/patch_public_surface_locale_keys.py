#!/usr/bin/env python3
"""Translate docs/discipline/utility keys when locale value still equals EN."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES
from scripts.build_locale_json import ALLOW_IDENTICAL, TRANSLATE_TARGETS, translate_value

PREFIXES = ("docs.", "discipline.", "utility.")


def main() -> None:
    keys = [k for k in EN if any(k.startswith(p) for p in PREFIXES)]
    locales_dir = ROOT / "locales"
    cache: dict[tuple[str, str], str] = {}
    for code in LOCALES:
        if code == "en":
            (locales_dir / "en.json").write_text(
                json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            continue
        path = locales_dir / f"{code}.json"
        cat = json.loads(path.read_text(encoding="utf-8"))
        for k in EN:
            cat.setdefault(k, EN[k])
        target = TRANSLATE_TARGETS.get(code)
        pending = [
            k
            for k in keys
            if cat.get(k, EN[k]) == EN[k] and k not in ALLOW_IDENTICAL
        ]
        if target and pending:
            print(f"{code}: {len(pending)} keys", flush=True)
            for key in pending:
                cat[key] = translate_value(EN[key], target, cache)
                time.sleep(0.05)
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {code}", flush=True)


if __name__ == "__main__":
    main()
