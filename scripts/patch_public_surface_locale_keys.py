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

from deep_translator import MyMemoryTranslator

from i18n_service import EN, LOCALES
from scripts.build_locale_json import ALLOW_IDENTICAL

MYMEMORY_TARGETS: dict[str, str] = {
    "es": "spanish",
    "ar": "arabic",
    "pt": "portuguese brazil",
    "fr": "french",
    "de": "german",
    "zh-CN": "chinese simplified",
    "zh-TW": "chinese traditional",
    "ja": "japanese",
    "ko": "korean",
    "hi": "hindi",
    "tr": "turkish",
    "ru": "russian",
    "id": "indonesian",
    "vi": "vietnamese",
    "th": "thai",
    "fil": "tagalog",
    "it": "italian",
    "bn": "bengali",
    "ur": "urdu",
    "fa": "persian",
    "ms": "malay",
    "pl": "polish",
    "nl": "dutch",
    "he": "hebrew",
}


def translate_value_mm(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    if not text or not text.strip():
        return text
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    try:
        out = MyMemoryTranslator(source="english", target=target).translate(text)
    except Exception:
        out = text
    cache[ck] = out or text
    return cache[ck]


PREFIXES = (
    "docs.",
    "discipline.",
    "utility.",
    "oracle.factor.",
    "oracle.source.",
    "oracle.share.copied",
    "trust.",
    "ui.why_",
    "ui.pending",
    "ui.copied",
    "ui.copy_",
    "ui.download_",
    "ui.certificate_",
    "ui.prediction_id",
    "ui.scenarios_title",
    "ui.verdict",
    "ui.id",
    "pulse.drawer.",
    "pulse.msg.",
    "pulse.chip.",
    "bounty.",
    "sealed.",
    "arb.",
    "ledger.panel.",
    "ledger.js.",
    "ledger.cta.bounty",
    "ledger.cta.sealed",
    "ledger.cta.audit",
    "ledger.cta.mev",
    "ledger.cta.locked",
    "meta.title.bounty",
    "meta.title.sealed",
)


def _key_matches(key: str) -> bool:
    for prefix in PREFIXES:
        if prefix.endswith("."):
            if key.startswith(prefix):
                return True
        elif key == prefix or key.startswith(prefix):
            return True
    return False


def main() -> None:
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
        target = MYMEMORY_TARGETS.get(code)
        pending = [
            k
            for k in EN
            if _key_matches(k)
            and cat.get(k, EN[k]) == EN[k]
            and k not in ALLOW_IDENTICAL
        ]
        if target and pending:
            print(f"{code}: {len(pending)} keys", flush=True)
            for key in pending:
                cat[key] = translate_value_mm(EN[key], target, cache)
                time.sleep(0.08)
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {code}", flush=True)


if __name__ == "__main__":
    main()
