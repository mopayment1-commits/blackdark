#!/usr/bin/env python3
"""Ensure every locales/*.json has all EN keys (missing keys default to English)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES, _load_json_catalog


def main() -> None:
    locales_dir = ROOT / "locales"
    (locales_dir / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for code in LOCALES:
        if code == "en":
            continue
        path = locales_dir / f"{code}.json"
        cat = dict(_load_json_catalog(code) or {})
        added = 0
        for k, v in EN.items():
            if k not in cat:
                cat[k] = v
                added += 1
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{code}: +{added} keys (total {len(cat)})")


if __name__ == "__main__":
    main()
