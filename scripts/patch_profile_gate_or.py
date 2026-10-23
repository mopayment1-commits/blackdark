#!/usr/bin/env python3
"""Localize profile.gate_or (English \"or\" is invalid for _translation_valid)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = ROOT / "locales"

GATE_OR: dict[str, str] = {
    "ar": "أو",
    "bn": "অথবা",
    "de": "oder",
    "es": "o",
    "fa": "یا",
    "fil": "o",
    "fr": "ou",
    "he": "או",
    "hi": "या",
    "id": "atau",
    "it": "oppure",
    "ja": "または",
    "ko": "또는",
    "ms": "atau",
    "nl": "of",
    "pl": "lub",
    "pt": "ou",
    "ru": "или",
    "th": "หรือ",
    "tr": "veya",
    "ur": "یا",
    "vi": "hoặc",
    "zh-CN": "或",
    "zh-TW": "或",
}


def main() -> None:
    for code, value in GATE_OR.items():
        path = LOCALES_DIR / f"{code}.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data["profile.gate_or"] = value
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("patched profile.gate_or for", len(GATE_OR), "locales")


if __name__ == "__main__":
    main()
