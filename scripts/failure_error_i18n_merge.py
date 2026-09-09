#!/usr/bin/env python3
"""Merge static error.* overlays into locales/*.json (no external MT)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from failure.error_i18n_static import ERROR_I18N_OVERLAYS  # noqa: E402
from i18n_service import EN, LOCALES  # noqa: E402

ERROR_KEYS = sorted(k for k in EN if k.startswith("error."))


def main() -> int:
    updated = 0
    for code in LOCALES:
        if code == "en":
            continue
        overlay = ERROR_I18N_OVERLAYS.get(code)
        if not overlay:
            print(f"missing overlay: {code}")
            return 1
        path = ROOT / "locales" / f"{code}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ERROR_KEYS:
            val = overlay.get(key)
            if not val or val == EN.get(key):
                print(f"bad overlay {code}:{key}")
                return 1
            data[key] = val
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
        print(f"updated {code}")
    print(f"done: {updated} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
